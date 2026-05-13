import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_invoice_pdf(invoice, booking, customer, fleet, owner) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.8 * cm, leftMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    orange = colors.HexColor("#E65100")
    light_grey = colors.HexColor("#F5F5F5")

    title_s  = ParagraphStyle("t", parent=styles["Heading1"], fontSize=18, textColor=orange, alignment=TA_LEFT, spaceAfter=2)
    sub_s    = ParagraphStyle("s", parent=styles["Normal"],   fontSize=9,  textColor=colors.grey, spaceAfter=2)
    label_s  = ParagraphStyle("l", parent=styles["Normal"],   fontSize=8,  textColor=colors.grey)
    value_s  = ParagraphStyle("v", parent=styles["Normal"],   fontSize=9,  spaceAfter=3)
    right_s  = ParagraphStyle("r", parent=styles["Normal"],   fontSize=9,  alignment=TA_RIGHT)
    total_s  = ParagraphStyle("tot", parent=styles["Normal"], fontSize=11, textColor=orange, alignment=TA_RIGHT)
    footer_s = ParagraphStyle("f", parent=styles["Normal"],   fontSize=7,  textColor=colors.grey, alignment=TA_CENTER)

    story = []

    # Header
    story.append(Paragraph("GOGOTRUK", title_s))
    story.append(Paragraph("Truk Truk India Pvt Ltd  |  Mumbai, Maharashtra", sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=orange, spaceAfter=10))

    # Invoice meta + customer in two columns
    invoice_date = invoice.created_at.strftime("%d %b %Y") if invoice.created_at else datetime.now().strftime("%d %b %Y")
    meta = [
        [Paragraph("<b>TAX INVOICE</b>", ParagraphStyle("h", parent=styles["Normal"], fontSize=13, textColor=orange)),
         Paragraph(f"Invoice No: <b>{invoice.invoice_number}</b>", right_s)],
        [Paragraph(f"Date: {invoice_date}", value_s),
         Paragraph(f"Booking ID: {booking.id}", right_s)],
    ]
    meta_table = Table(meta, colWidths=["50%", "50%"])
    meta_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # Bill to / Ship details
    customer_name = f"{customer.first_name} {customer.last_name}"
    bill_data = [
        [Paragraph("<b>BILLED TO</b>", label_s), Paragraph("<b>SHIPMENT DETAILS</b>", label_s)],
        [Paragraph(customer_name, value_s), Paragraph(f"Vehicle: {fleet.vehicle_type}", value_s)],
        [Paragraph(customer.mobile, value_s), Paragraph(f"Reg No: {fleet.registration_number}", value_s)],
        [Paragraph(customer.email, value_s), Paragraph(f"Owner: {owner.first_name} {owner.last_name}", value_s)],
        [Paragraph(f"Pickup: {booking.pickup_address}", value_s), Paragraph(f"Date: {booking.booking_date}", value_s)],
        [Paragraph(f"Delivery: {booking.destination_address}", value_s), Paragraph(f"Distance: {invoice.distance_km} km", value_s)],
    ]
    bill_table = Table(bill_data, colWidths=["50%", "50%"])
    bill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), light_grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 0.5 * cm))

    # Goods
    story.append(Paragraph("<b>GOODS DETAILS</b>", label_s))
    story.append(Paragraph(f"{booking.goods_type}  |  {booking.goods_weight_kg} kg", value_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=8))

    # Charges table
    charge_data = [
        [Paragraph("<b>Description</b>", label_s), Paragraph("<b>Amount (₹)</b>", ParagraphStyle("rh", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_RIGHT))],
        ["Base Freight Charge", f"₹ {invoice.base_fare:,.2f}"],
        ["Waiting Charges", f"₹ {invoice.waiting_charges:,.2f}"],
        ["Toll Charges", f"₹ {invoice.toll_charges:,.2f}"],
        ["Loading / Unloading Charges", f"₹ {invoice.loading_charges:,.2f}"],
        [Paragraph("<b>Subtotal (before GST)</b>", ParagraphStyle("bold", parent=styles["Normal"], fontSize=9)), Paragraph(f"<b>₹ {invoice.total_before_gst:,.2f}</b>", ParagraphStyle("boldr", parent=styles["Normal"], fontSize=9, alignment=TA_RIGHT))],
    ]

    if invoice.gst_type == "IGST":
        charge_data.append([f"IGST @ {invoice.igst_rate}%", f"₹ {invoice.igst_amount:,.2f}"])
    else:
        charge_data.append([f"CGST @ {invoice.cgst_rate}%", f"₹ {invoice.cgst_amount:,.2f}"])
        charge_data.append([f"SGST @ {invoice.sgst_rate}%", f"₹ {invoice.sgst_amount:,.2f}"])

    charges_table = Table(charge_data, colWidths=["70%", "30%"])
    charges_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), light_grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.lightgrey),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(charges_table)
    story.append(Spacer(1, 0.2 * cm))

    # Total
    story.append(Paragraph(f"TOTAL AMOUNT: ₹ {invoice.total_amount:,.2f}", total_s))
    story.append(HRFlowable(width="100%", thickness=2, color=orange, spaceBefore=6, spaceAfter=10))

    story.append(Paragraph(
        "This is a computer-generated invoice. No signature required.  |  "
        "GoGoTruk — Truk Truk India Pvt Ltd  |  Mumbai, Maharashtra",
        footer_s
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
