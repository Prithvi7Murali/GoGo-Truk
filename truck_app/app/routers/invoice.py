from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import io

from app.database import get_db
from app.schemas.invoice import InvoiceCreate, PricingPreview, InvoiceResponse
from app.models.invoice import Invoice
from app.models.booking import Booking
from app.models.fleet import Fleet
from app.models.kyc import CustomerKYC, OwnerKYC
from app.utils.pricing import get_applicable_rate, calculate_fare, calculate_gst
from app.utils.invoice_pdf import generate_invoice_pdf
from app.utils.cloudinary_client import upload_pdf_doc
from app.config import settings

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


def _invoice_number(booking_id: int) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"INV-{date_str}-{booking_id:06d}"


def _build_invoice_data(data: InvoiceCreate, booking: Booking, fleet: Fleet, db: Session) -> dict:
    rate = get_applicable_rate(db, fleet.vehicle_type, data.distance_km)
    if not rate:
        raise HTTPException(
            status_code=400,
            detail=f"No active rate card found for vehicle type '{fleet.vehicle_type}' at {data.distance_km} km"
        )

    base_fare         = round(calculate_fare(rate, data.distance_km), 2)
    total_before_gst  = round(base_fare + data.waiting_charges + data.toll_charges + data.loading_charges, 2)
    gst               = calculate_gst(total_before_gst, data.gst_type, data.gst_rate)
    total_gst         = round(gst["cgst_amount"] + gst["sgst_amount"] + gst["igst_amount"], 2)
    total_amount      = round(total_before_gst + total_gst, 2)

    return dict(
        invoice_number   = _invoice_number(booking.id),
        booking_id       = booking.id,
        customer_kyc_id  = booking.customer_kyc_id,
        distance_km      = data.distance_km,
        base_fare        = base_fare,
        waiting_charges  = data.waiting_charges,
        toll_charges     = data.toll_charges,
        loading_charges  = data.loading_charges,
        total_before_gst = total_before_gst,
        gst_type         = data.gst_type,
        total_amount     = total_amount,
        **gst,
    )


def _send_invoice_email(invoice_id: int):
    from app.database import SessionLocal
    from app.utils.notifier import notify_invoice_sent

    db = SessionLocal()
    try:
        invoice  = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        customer = db.query(CustomerKYC).filter(CustomerKYC.id == invoice.customer_kyc_id).first()
        if invoice and customer:
            notify_invoice_sent(customer, invoice)
            invoice.status = "Sent"
            db.commit()
    finally:
        db.close()


@router.post("/preview")
def preview_pricing(data: PricingPreview, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    fleet = db.query(Fleet).filter(Fleet.id == booking.fleet_id).first()

    rate = get_applicable_rate(db, fleet.vehicle_type, data.distance_km)
    if not rate:
        raise HTTPException(status_code=400, detail=f"No active rate card for '{fleet.vehicle_type}' at {data.distance_km} km")

    base_fare        = round(calculate_fare(rate, data.distance_km), 2)
    total_before_gst = round(base_fare + data.waiting_charges + data.toll_charges + data.loading_charges, 2)
    gst              = calculate_gst(total_before_gst, data.gst_type, data.gst_rate)
    total_gst        = round(gst["cgst_amount"] + gst["sgst_amount"] + gst["igst_amount"], 2)

    return {
        "vehicle_type":     fleet.vehicle_type,
        "distance_km":      data.distance_km,
        "rate_per_km":      rate.rate_per_km,
        "base_fare":        base_fare,
        "waiting_charges":  data.waiting_charges,
        "toll_charges":     data.toll_charges,
        "loading_charges":  data.loading_charges,
        "total_before_gst": total_before_gst,
        "gst_type":         data.gst_type,
        **gst,
        "total_gst":        total_gst,
        "total_amount":     round(total_before_gst + total_gst, 2),
    }


@router.post("/generate", response_model=InvoiceResponse, status_code=201)
def generate_invoice(data: InvoiceCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "Confirmed":
        raise HTTPException(status_code=409, detail="Invoice can only be generated for Confirmed bookings")

    existing = db.query(Invoice).filter(Invoice.booking_id == data.booking_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Invoice already exists for this booking")

    fleet    = db.query(Fleet).filter(Fleet.id == booking.fleet_id).first()
    customer = db.query(CustomerKYC).filter(CustomerKYC.id == booking.customer_kyc_id).first()
    owner    = db.query(OwnerKYC).filter(OwnerKYC.id == fleet.owner_kyc_id).first()

    invoice_data = _build_invoice_data(data, booking, fleet, db)
    invoice = Invoice(**invoice_data)
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Generate PDF and upload to Cloudinary
    try:
        pdf_bytes = generate_invoice_pdf(invoice, booking, customer, fleet, owner)
        pdf_url   = upload_pdf_doc(pdf_bytes, "gogotruk/invoices")
        invoice.invoice_pdf_url = pdf_url
        db.commit()
        db.refresh(invoice)
    except Exception as e:
        print(f"[invoice] PDF generation failed: {e}")

    background_tasks.add_task(_send_invoice_email, invoice.id)
    return invoice


@router.get("/booking/{booking_id}", response_model=InvoiceResponse)
def get_invoice_by_booking(booking_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.booking_id == booking_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found for this booking")
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    booking  = db.query(Booking).filter(Booking.id == invoice.booking_id).first()
    fleet    = db.query(Fleet).filter(Fleet.id == booking.fleet_id).first()
    customer = db.query(CustomerKYC).filter(CustomerKYC.id == invoice.customer_kyc_id).first()
    owner    = db.query(OwnerKYC).filter(OwnerKYC.id == fleet.owner_kyc_id).first()

    pdf_bytes = generate_invoice_pdf(invoice, booking, customer, fleet, owner)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={invoice.invoice_number}.pdf"},
    )
