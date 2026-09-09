from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_invoice_pdf(invoice):
    """
    Generates a professional PDF invoice in-memory using ReportLab.
    Returns a BytesIO buffer.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10
    )

    bold_style = ParagraphStyle(
        'BoldText',
        parent=normal_style,
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14
    )

    story = []

    # 1. Header: Company Brand & Document Title
    header_data = [
        [
            Paragraph("<b>PropertyLedger Management</b><br/>123 Real Estate Blvd<br/>billing@propertyledger.com", normal_style),
            Paragraph(f"<b>INVOICE</b><br/>#INV-{invoice.id}<br/>Date: {invoice.invoice_date.strftime('%Y-%m-%d')}", title_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[300, 240])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # 2. Billed To & Lease Specifics
    tenant = invoice.lease.tenant
    unit = invoice.lease.unit

    billing_info_data = [
        [
            Paragraph(
                f"<b>Billed To:</b><br/>"
                f"{tenant.first_name} {tenant.last_name}<br/>"
                f"{tenant.email}<br/>"
                f"{tenant.phone}",
                normal_style
            ),
            Paragraph(
                f"<b>Lease & Due Info:</b><br/>"
                f"<b>Unit:</b> {unit.unit_number} ({unit.floor_plan})<br/>"
                f"<b>Due Date:</b> {invoice.due_date.strftime('%Y-%m-%d')}<br/>"
                f"<b>Status:</b> {invoice.status.replace('_', ' ').title()}",
                normal_style
            )
        ]
    ]
    billing_table = Table(billing_info_data, colWidths=[300, 240])
    billing_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(billing_table)
    story.append(Spacer(1, 25))

    # 3. Itemized Charges Table
    charge_title = invoice.charge_type.replace('_', ' ').title()
    items_data = [
        [
            Paragraph("<b>Description</b>", bold_style),
            Paragraph("<b>Due Date</b>", bold_style),
            Paragraph("<b>Amount Due</b>", bold_style)
        ],
        [
            Paragraph(f"{charge_title} - Unit {unit.unit_number}", normal_style),
            Paragraph(invoice.due_date.strftime('%Y-%m-%d'), normal_style),
            f"${float(invoice.amount_due):.2f}"
        ],
        [
            "",
            Paragraph("<b>Total Due:</b>", bold_style),
            f"${float(invoice.amount_due):.2f}"
        ],
        [
            "",
            Paragraph("<b>Amount Paid:</b>", bold_style),
            f"${float(invoice.amount_paid):.2f}"
        ],
        [
            "",
            Paragraph("<b>Balance Remaining:</b>", bold_style),
            f"${float(invoice.amount_due - invoice.amount_paid):.2f}"
        ]
    ]

    items_table = Table(items_data, colWidths=[280, 130, 130])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#cbd5e1")),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor("#e2e8f0")),
        ('LINEABOVE', (1, 2), (-1, 2), 1, colors.HexColor("#cbd5e1")),
    ]))
    story.append(items_table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer