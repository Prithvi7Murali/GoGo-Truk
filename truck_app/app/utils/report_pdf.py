import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

ORANGE = colors.HexColor("#E87820")
LIGHT_ORANGE = colors.HexColor("#FFF3E0")
GREY = colors.HexColor("#757575")
LIGHT_GREY = colors.HexColor("#F5F5F5")


def _base_doc(buffer, landscape_mode=False):
    pagesize = landscape(A4) if landscape_mode else A4
    return SimpleDocTemplate(
        buffer, pagesize=pagesize,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )


def _header(story, title: str, subtitle: str, styles):
    title_s = ParagraphStyle("t", parent=styles["Heading1"], fontSize=16, textColor=ORANGE, spaceAfter=2)
    sub_s   = ParagraphStyle("s", parent=styles["Normal"],   fontSize=8,  textColor=GREY,   spaceAfter=4)
    story.append(Paragraph("GOGOTRUK", title_s))
    story.append(Paragraph(f"{title}  |  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}", sub_s))
    if subtitle:
        story.append(Paragraph(subtitle, sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE, spaceAfter=8))


def _table(data, col_widths, landscape_mode=False):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  ORANGE),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  8),
        ("FONTSIZE",    (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#E0E0E0")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# ── KYC Report ────────────────────────────────────────────────────────────────

def generate_kyc_pdf(records: list) -> bytes:
    buffer = io.BytesIO()
    doc = _base_doc(buffer, landscape_mode=True)
    styles = getSampleStyleSheet()
    story = []

    _header(story, "KYC Queue Report", f"Total records: {len(records)}", styles)

    headers = ["#", "Full Name", "Type", "Mobile", "Email", "City", "State", "Status", "Submitted"]
    page_w = landscape(A4)[0] - 3 * cm
    col_widths = [
        page_w * 0.04,
        page_w * 0.14,
        page_w * 0.09,
        page_w * 0.10,
        page_w * 0.16,
        page_w * 0.09,
        page_w * 0.09,
        page_w * 0.09,
        page_w * 0.10,
    ]

    rows = [headers]
    for i, r in enumerate(records, 1):
        submitted = r.get("submitted_at", "")
        if submitted and hasattr(submitted, "strftime"):
            submitted = submitted.strftime("%d %b %Y")
        rows.append([
            str(i),
            r.get("full_name", ""),
            r.get("customer_type", ""),
            r.get("mobile", ""),
            r.get("email", ""),
            r.get("city", "") or "—",
            r.get("state", "") or "—",
            r.get("status", ""),
            str(submitted)[:10] if submitted else "—",
        ])

    story.append(_table(rows, col_widths, landscape_mode=True))
    doc.build(story)
    return buffer.getvalue()


# ── Bookings Report ───────────────────────────────────────────────────────────

def generate_bookings_pdf(records: list) -> bytes:
    buffer = io.BytesIO()
    doc = _base_doc(buffer, landscape_mode=True)
    styles = getSampleStyleSheet()
    story = []

    _header(story, "Bookings Report", f"Total records: {len(records)}", styles)

    headers = ["#", "ID", "Customer", "Owner", "Vehicle No.", "Pickup", "Drop", "Date", "Goods", "Wt(kg)", "Status"]
    page_w = landscape(A4)[0] - 3 * cm
    col_widths = [
        page_w * 0.03,
        page_w * 0.04,
        page_w * 0.10,
        page_w * 0.10,
        page_w * 0.09,
        page_w * 0.12,
        page_w * 0.12,
        page_w * 0.08,
        page_w * 0.10,
        page_w * 0.06,
        page_w * 0.08,
    ]

    rows = [headers]
    for i, r in enumerate(records, 1):
        rows.append([
            str(i),
            str(r.get("id", "")),
            r.get("customer_name", ""),
            r.get("owner_name", ""),
            r.get("vehicle_number", ""),
            r.get("pickup_address", "")[:30],
            r.get("destination_address", "")[:30],
            str(r.get("booking_date", ""))[:10],
            r.get("goods_type", "")[:20],
            str(r.get("goods_weight_kg", "")),
            r.get("status", ""),
        ])

    story.append(_table(rows, col_widths, landscape_mode=True))
    doc.build(story)
    return buffer.getvalue()


# ── Revenue Report ────────────────────────────────────────────────────────────

def generate_revenue_pdf(records: list, totals: dict) -> bytes:
    buffer = io.BytesIO()
    doc = _base_doc(buffer, landscape_mode=True)
    styles = getSampleStyleSheet()
    story = []

    subtitle = (
        f"Total records: {len(records)}  |  "
        f"Total invoiced: ₹{totals.get('total_invoiced', 0):,.2f}  |  "
        f"Paid: ₹{totals.get('total_paid', 0):,.2f}  |  "
        f"Outstanding: ₹{totals.get('outstanding', 0):,.2f}"
    )
    _header(story, "Revenue Report", subtitle, styles)

    headers = ["#", "Invoice No.", "Booking ID", "Customer", "Base Fare", "GST Type", "CGST", "SGST", "IGST", "Total", "Status", "Date"]
    page_w = landscape(A4)[0] - 3 * cm
    col_widths = [
        page_w * 0.03,
        page_w * 0.11,
        page_w * 0.07,
        page_w * 0.11,
        page_w * 0.08,
        page_w * 0.07,
        page_w * 0.06,
        page_w * 0.06,
        page_w * 0.06,
        page_w * 0.08,
        page_w * 0.07,
        page_w * 0.08,
    ]

    rows = [headers]
    for i, r in enumerate(records, 1):
        rows.append([
            str(i),
            r.get("invoice_number", ""),
            str(r.get("booking_id", "")),
            r.get("customer_name", ""),
            f"₹{r.get('base_fare', 0):,.2f}",
            r.get("gst_type", ""),
            f"₹{r.get('cgst_amount', 0):,.2f}",
            f"₹{r.get('sgst_amount', 0):,.2f}",
            f"₹{r.get('igst_amount', 0):,.2f}",
            f"₹{r.get('total_amount', 0):,.2f}",
            r.get("status", ""),
            str(r.get("generated_at", ""))[:10],
        ])

    story.append(_table(rows, col_widths, landscape_mode=True))
    doc.build(story)
    return buffer.getvalue()
