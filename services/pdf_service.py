"""
PDF Service – generates a formatted monthly expense report using ReportLab.
"""
from datetime import datetime
from io import BytesIO
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# Brand colour palette
PRIMARY = colors.HexColor("#4F46E5")   # indigo
ACCENT = colors.HexColor("#7C3AED")    # violet
LIGHT_BG = colors.HexColor("#F5F3FF")
GREY = colors.HexColor("#6B7280")
DARK = colors.HexColor("#111827")
WHITE = colors.white


def inr(amount: float) -> str:
    return f"₹{amount:,.2f}"


def generate_monthly_report(user: dict, receipts: List[dict], year: int, month: int) -> bytes:
    """Generate a PDF expense report and return it as bytes.

    Parameters
    ----------
    user : dict
        MongoDB user document (must contain 'name' and 'email').
    receipts : list
        List of MongoDB receipt documents for the target month.
    year : int
        Report year.
    month : int
        Report month (1-12).

    Returns
    -------
    bytes
        Raw PDF bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"ExpenseEye – Expense Report {year}-{month:02d}",
    )

    styles = getSampleStyleSheet()
    story = []

    # ------------------------------------------------------------------ Header
    title_style = ParagraphStyle(
        "title", parent=styles["Title"],
        fontSize=22, textColor=PRIMARY, spaceAfter=4,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "subtitle", parent=styles["Normal"],
        fontSize=11, textColor=GREY, spaceAfter=2,
        alignment=TA_CENTER,
    )
    month_name = datetime(year, month, 1).strftime("%B %Y")

    story.append(Paragraph("Expense Eye", title_style))
    story.append(Paragraph("Intelligent Expense Manager", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.3 * cm))

    # ------------------------------------------------------------------ Meta
    meta_style = ParagraphStyle("meta", parent=styles["Normal"], fontSize=10, textColor=DARK)
    story.append(Paragraph(f"<b>Report Period:</b> {month_name}", meta_style))
    story.append(Paragraph(f"<b>Prepared for:</b> {user.get('name', 'User')} ({user.get('email', '')})", meta_style))
    story.append(Paragraph(f"<b>Generated on:</b> {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}", meta_style))
    story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------------------ Summary
    total_spent = sum(r.get("total", 0) for r in receipts)
    total_tax = sum(r.get("tax", 0) for r in receipts)
    num_receipts = len(receipts)

    # Category breakdown
    cat_totals: dict = {}
    for r in receipts:
        cat = r.get("category", "Other")
        cat_totals[cat] = cat_totals.get(cat, 0) + r.get("total", 0)
    top_cat = max(cat_totals, key=cat_totals.get) if cat_totals else "N/A"

    summary_data = [
        ["Total Spent", inr(total_spent)],
        ["Total Tax", inr(total_tax)],
        ["Receipts", str(num_receipts)],
        ["Top Category", top_cat],
    ]
    summary_table = Table(summary_data, colWidths=[6 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_BG]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))

    section_heading = ParagraphStyle(
        "sh", parent=styles["Heading2"],
        fontSize=13, textColor=PRIMARY, spaceBefore=14, spaceAfter=4,
    )
    story.append(Paragraph("Summary", section_heading))
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------------------ Category breakdown table
    if cat_totals:
        story.append(Paragraph("Spending by Category", section_heading))
        cat_headers = ["Category", "Amount", "% of Total"]
        cat_rows = [cat_headers]
        for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1]):
            pct = (amt / total_spent * 100) if total_spent else 0
            cat_rows.append([cat, inr(amt), f"{pct:.1f}%"])

        cat_table = Table(cat_rows, colWidths=[8 * cm, 5 * cm, 5 * cm])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------------------ Receipt ledger
    story.append(Paragraph("Receipt Details", section_heading))
    receipt_headers = ["Date", "Vendor", "Category", "Tax", "Total"]
    receipt_rows = [receipt_headers]
    for r in sorted(receipts, key=lambda x: x.get("receipt_date", "")):
        receipt_rows.append([
            r.get("receipt_date", "N/A"),
            r.get("vendor", "Unknown")[:30],
            r.get("category", "Other"),
            inr(r.get('tax', 0)),
            inr(r.get('total', 0)),
        ])
    # Totals row
    receipt_rows.append(["", "", "TOTAL", inr(total_tax), inr(total_spent)])

    col_widths = [3 * cm, 6 * cm, 4 * cm, 3 * cm, 3 * cm]
    receipt_table = Table(receipt_rows, colWidths=col_widths, repeatRows=1)
    receipt_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BG),
        ("TEXTCOLOR", (0, -1), (-1, -1), PRIMARY),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (3, 0), (4, -1), "RIGHT"),
    ]))
    story.append(receipt_table)
    story.append(Spacer(1, 1 * cm))

    # ------------------------------------------------------------------ Footer
    footer_style = ParagraphStyle(
        "footer", parent=styles["Normal"],
        fontSize=8, textColor=GREY, alignment=TA_CENTER,
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREY))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Generated by Expense Eye – Intelligent Expense Manager", footer_style))

    doc.build(story)
    return buffer.getvalue()
