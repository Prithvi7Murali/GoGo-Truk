from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import io

DECLARATION_VERSION = "1.0"

DECLARATION_TEXT = """
1. GOODS LIABILITY
The customer declares that all goods submitted for transport are legally owned or authorized for transport by them. GoGoTruk (Truk Truk India Pvt Ltd) bears no liability for loss, damage, or theft of goods unless caused by proven negligence of the assigned truck owner. The customer agrees to declare the accurate nature and value of goods at the time of booking.

2. PACKAGING RESPONSIBILITY
The customer is solely responsible for ensuring goods are appropriately packed and secured for road transport. Damage resulting from inadequate packaging is entirely the customer's responsibility. GoGoTruk and its truck owners will not be held liable for damage caused by improper packing.

3. PAYMENT TERMS
The customer agrees to pay the full freight charges as quoted at the time of booking confirmation. Payments must be completed before or upon delivery as per the selected payment method. Disputed payments must be raised within 48 hours of delivery. Late payments attract a penalty of 2% per week on the outstanding amount.

4. CANCELLATION POLICY
Cancellation more than 48 hours before scheduled pickup: No cancellation charge.
Cancellation between 24 and 48 hours before pickup: 25% of the freight charge is retained.
Cancellation less than 24 hours before pickup: 50% of the freight charge is retained.
No-show on the day of pickup without prior notice: 100% of the freight charge is forfeited.
Refunds for eligible cancellations will be processed within 5-7 business days.

5. LEGAL COMPLIANCE
The customer confirms that all goods being transported fully comply with applicable Indian laws and regulations. Transport of prohibited, hazardous, explosive, narcotic, counterfeit, or otherwise illegal goods is strictly prohibited. Violation of this clause will result in immediate account suspension, forfeiture of all payments, and referral to law enforcement authorities.

6. DISPUTE RESOLUTION
Any disputes arising from the use of the GoGoTruk platform shall be subject to the exclusive jurisdiction of the competent courts in Mumbai, Maharashtra, India. Both parties agree to attempt resolution through mediation before initiating legal proceedings.

7. PLATFORM USAGE
The customer agrees to use the GoGoTruk platform only for lawful purposes. Misuse of the platform, including fraudulent bookings, false declarations, or abuse of the cancellation policy, will result in permanent account ban without refund.
"""


def generate_consent_pdf(
    customer_name: str,
    mobile: str,
    email: str,
    ip_address: str,
    device_info: str,
    timestamp: str,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=16, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "subtitle", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10, textColor=colors.grey, spaceAfter=4
    )
    section_style = ParagraphStyle(
        "body", parent=styles["Normal"], fontSize=9, alignment=TA_JUSTIFY, spaceAfter=8, leading=14
    )
    label_style = ParagraphStyle(
        "label", parent=styles["Normal"], fontSize=9, textColor=colors.grey
    )
    value_style = ParagraphStyle(
        "value", parent=styles["Normal"], fontSize=10, spaceAfter=4
    )

    story = []

    story.append(Paragraph("TRUK TRUK — CUSTOMER DECLARATION & DIGITAL CONSENT", title_style))
    story.append(Paragraph(f"Declaration Version {DECLARATION_VERSION}  |  Effective April 2026", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.orange, spaceAfter=12))

    story.append(Paragraph("CUSTOMER DETAILS", styles["Heading3"]))
    story.append(Paragraph("Name", label_style))
    story.append(Paragraph(customer_name, value_style))
    story.append(Paragraph("Mobile", label_style))
    story.append(Paragraph(mobile, value_style))
    story.append(Paragraph("Email", label_style))
    story.append(Paragraph(email, value_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=12))

    story.append(Paragraph("DECLARATION TERMS", styles["Heading3"]))
    for para in DECLARATION_TEXT.strip().split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), section_style))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.orange, spaceBefore=12, spaceAfter=12))

    story.append(Paragraph("ACCEPTANCE RECORD", styles["Heading3"]))
    story.append(Paragraph("I have read, understood, and agree to all the terms stated in this declaration.", section_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Accepted By", label_style))
    story.append(Paragraph(customer_name, value_style))
    story.append(Paragraph("Acceptance Timestamp (IST)", label_style))
    story.append(Paragraph(timestamp, value_style))
    story.append(Paragraph("IP Address", label_style))
    story.append(Paragraph(ip_address, value_style))
    story.append(Paragraph("Device / Browser", label_style))
    story.append(Paragraph(device_info or "Not captured", value_style))
    story.append(Paragraph("Declaration Version", label_style))
    story.append(Paragraph(DECLARATION_VERSION, value_style))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceBefore=12, spaceAfter=8))
    story.append(Paragraph(
        "This document is a legally binding digital record of consent. Generated and stored by Truk Truk India Pvt Ltd.",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
