import os
import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_invoice_pdf(billing_data):
    """
    Generate a professional PDF invoice.
    Returns bytes of the PDF or None on failure.
    """
    if not REPORTLAB_AVAILABLE:
        return None

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )

        # ── Colours ───────────────────────────────────
        PURPLE      = colors.HexColor('#7C3AED')
        PURPLE_DARK = colors.HexColor('#5B21B6')
        PURPLE_LIGHT= colors.HexColor('#EDE9FE')
        GREEN       = colors.HexColor('#059669')
        RED         = colors.HexColor('#DC2626')
        GRAY_LIGHT  = colors.HexColor('#F9FAFB')
        GRAY        = colors.HexColor('#6B7280')
        BLACK       = colors.HexColor('#111827')

        styles = getSampleStyleSheet()

        # ── Custom Paragraph Styles ───────────────────
        def make_style(name, **kwargs):
            return ParagraphStyle(name, parent=styles['Normal'], **kwargs)

        title_style   = make_style('Title',   fontSize=22, textColor=PURPLE,
                                   fontName='Helvetica-Bold')
        header_style  = make_style('Header',  fontSize=10, textColor=colors.white,
                                   fontName='Helvetica-Bold', alignment=TA_CENTER)
        normal_style  = make_style('Norm',    fontSize=9,  textColor=BLACK)
        small_style   = make_style('Small',   fontSize=8,  textColor=GRAY)
        bold_style    = make_style('Bold',    fontSize=9,  textColor=BLACK,
                                   fontName='Helvetica-Bold')
        right_style   = make_style('Right',   fontSize=9,  textColor=BLACK,
                                   alignment=TA_RIGHT)
        right_bold    = make_style('RightBold', fontSize=10, textColor=PURPLE,
                                   fontName='Helvetica-Bold', alignment=TA_RIGHT)
        center_style  = make_style('Center',  fontSize=9,  alignment=TA_CENTER)

        story = []

        # ── HEADER BANNER ─────────────────────────────
        header_data = [[
            Paragraph(
                billing_data.get('business_name', 'Event Planner Pro'),
                make_style('BizName', fontSize=16, textColor=colors.white,
                           fontName='Helvetica-Bold')
            ),
            Paragraph(
                f"INVOICE<br/><font size='11'>{billing_data.get('invoice_number', '')}</font>",
                make_style('InvNo', fontSize=14, textColor=colors.white,
                           fontName='Helvetica-Bold', alignment=TA_RIGHT)
            )
        ]]
        header_table = Table(header_data, colWidths=[100*mm, 65*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,-1), PURPLE_DARK),
            ('PADDING',     (0,0), (-1,-1), 10),
            ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 6*mm))

        # ── BILL TO & EVENT DETAILS ───────────────────
        bill_to = billing_data.get('customer_name', '—')
        phone   = billing_data.get('customer_phone', '—')
        email   = billing_data.get('customer_email', '—')
        address = billing_data.get('customer_address', '—')

        event_type     = billing_data.get('event_type', '—')
        event_date     = billing_data.get('event_date', '—')
        event_duration = billing_data.get('event_duration', 1)
        invoice_date   = billing_data.get('created_at',
                            datetime.now().strftime('%d %b %Y'))

        info_data = [
            [
                Paragraph('<b>Bill To:</b>', bold_style),
                Paragraph('<b>Event Details:</b>', bold_style),
                Paragraph('<b>Invoice Info:</b>', bold_style)
            ],
            [
                Paragraph(f"{bill_to}<br/>{phone}<br/>{email}<br/>{address}", normal_style),
                Paragraph(f"Type: {event_type}<br/>Date: {event_date}<br/>Duration: {event_duration} day(s)", normal_style),
                Paragraph(f"Invoice #: {billing_data.get('invoice_number','')}<br/>Date: {invoice_date}<br/>Status: {billing_data.get('billing_status','')}", normal_style),
            ]
        ]
        info_table = Table(info_data, colWidths=[60*mm, 60*mm, 45*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0), PURPLE_LIGHT),
            ('PADDING',     (0,0), (-1,-1), 7),
            ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0,0), (-1,-1), 9),
            ('VALIGN',      (0,0), (-1,-1), 'TOP'),
            ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, GRAY_LIGHT]),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 6*mm))

        # ── SERVICE ITEMS TABLE ───────────────────────
        items = billing_data.get('items', [])
        if items:
            story.append(Paragraph('Service Charges', bold_style))
            story.append(Spacer(1, 2*mm))

            item_rows = [[
                Paragraph('#',           header_style),
                Paragraph('Service',     header_style),
                Paragraph('Qty',         header_style),
                Paragraph('Unit Price',  header_style),
                Paragraph('Total',       header_style),
            ]]
            for i, item in enumerate(items, 1):
                item_rows.append([
                    Paragraph(str(i), center_style),
                    Paragraph(str(item.get('service_name', '')), normal_style),
                    Paragraph(str(item.get('quantity', 1)), center_style),
                    Paragraph(f"Rs.{float(item.get('unit_price', 0)):,.0f}", right_style),
                    Paragraph(f"Rs.{float(item.get('total_price', 0)):,.0f}", right_style),
                ])

            items_table = Table(
                item_rows,
                colWidths=[12*mm, 70*mm, 18*mm, 30*mm, 30*mm]
            )
            items_table.setStyle(TableStyle([
                ('BACKGROUND',  (0,0), (-1,0), PURPLE),
                ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
                ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',    (0,0), (-1,-1), 9),
                ('PADDING',     (0,0), (-1,-1), 6),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, GRAY_LIGHT]),
                ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('ALIGN',       (2,0), (-1,-1), 'CENTER'),
                ('ALIGN',       (3,1), (-1,-1), 'RIGHT'),
                ('ALIGN',       (4,1), (-1,-1), 'RIGHT'),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 4*mm))

        # ── LABOUR & MATERIAL TABLE ───────────────────
        labour_cost = float(billing_data.get('total_labour_cost', 0))
        flower      = float(billing_data.get('flower_cost', 0))
        cloth       = float(billing_data.get('cloth_banner_cost', 0))
        electrical  = float(billing_data.get('electrical_materials_cost', 0))
        rental      = float(billing_data.get('rental_items_cost', 0))
        other_mat   = float(billing_data.get('other_material_cost', 0))

        cost_rows = []
        n_lab  = billing_data.get('number_of_labours', 0)
        l_wage = billing_data.get('labour_daily_wage', 0)
        l_days = billing_data.get('labour_days', 1)

        if labour_cost > 0:
            cost_rows.append([
                f"Labour ({n_lab} × Rs.{l_wage}/day × {l_days} days)",
                f"Rs.{labour_cost:,.0f}"
            ])
        for label, val in [
            ('Flower Cost',           flower),
            ('Cloth / Banner',        cloth),
            ('Electrical Materials',  electrical),
            ('Rental Items',          rental),
            ('Other Materials',       other_mat),
        ]:
            if val > 0:
                cost_rows.append([label, f"Rs.{val:,.0f}"])

        if cost_rows:
            story.append(Paragraph('Labour & Material Costs', bold_style))
            story.append(Spacer(1, 2*mm))

            cost_header = [[
                Paragraph('Description', header_style),
                Paragraph('Amount',      header_style),
            ]]
            all_cost_rows = cost_header + [
                [Paragraph(r[0], normal_style),
                 Paragraph(r[1], right_style)]
                for r in cost_rows
            ]
            cost_table = Table(
                all_cost_rows,
                colWidths=[125*mm, 40*mm]
            )
            cost_table.setStyle(TableStyle([
                ('BACKGROUND',     (0,0), (-1,0), PURPLE),
                ('TEXTCOLOR',      (0,0), (-1,0), colors.white),
                ('FONTNAME',       (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',       (0,0), (-1,-1), 9),
                ('PADDING',        (0,0), (-1,-1), 6),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, GRAY_LIGHT]),
                ('GRID',           (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('ALIGN',          (1,1), (-1,-1), 'RIGHT'),
            ]))
            story.append(cost_table)
            story.append(Spacer(1, 4*mm))

        # ── PAYMENT SUMMARY ───────────────────────────
        subtotal      = float(billing_data.get('subtotal', 0))
        discount      = float(billing_data.get('discount', 0))
        tax_rate      = float(billing_data.get('tax_rate', 0))
        tax_amount    = float(billing_data.get('tax_amount', 0))
        grand_total   = float(billing_data.get('grand_total', 0))
        advance_paid  = float(billing_data.get('advance_paid', 0))
        pending       = float(billing_data.get('pending_amount', 0))
        payment_mode  = billing_data.get('payment_mode', 'Cash')

        summary_rows = [
            ['Subtotal',        f"Rs.{subtotal:,.2f}"],
        ]
        if discount > 0:
            summary_rows.append(['Discount',   f"- Rs.{discount:,.2f}"])
        if tax_rate > 0:
            summary_rows.append([f"GST ({tax_rate}%)", f"Rs.{tax_amount:,.2f}"])

        summary_data = [
            [Paragraph('Payment Summary', make_style(
                'SumHeader', fontSize=10, textColor=colors.white,
                fontName='Helvetica-Bold'
            )), '']
        ]
        for row in summary_rows:
            summary_data.append([
                Paragraph(row[0], normal_style),
                Paragraph(row[1], right_style)
            ])

        summary_data.append([
            Paragraph('Grand Total', make_style(
                'GTLabel', fontSize=11, fontName='Helvetica-Bold',
                textColor=PURPLE
            )),
            Paragraph(f"Rs.{grand_total:,.2f}", make_style(
                'GTVal', fontSize=11, fontName='Helvetica-Bold',
                textColor=PURPLE, alignment=TA_RIGHT
            ))
        ])
        summary_data.append([
            Paragraph('Advance Paid', normal_style),
            Paragraph(f"Rs.{advance_paid:,.2f}", right_style)
        ])
        summary_data.append([
            Paragraph('Balance Due', make_style(
                'BalLabel', fontSize=11, fontName='Helvetica-Bold',
                textColor=RED
            )),
            Paragraph(f"Rs.{pending:,.2f}", make_style(
                'BalVal', fontSize=11, fontName='Helvetica-Bold',
                textColor=RED, alignment=TA_RIGHT
            ))
        ])
        summary_data.append([
            Paragraph('Payment Mode', small_style),
            Paragraph(payment_mode, right_style)
        ])

        # Right-align the summary table
        summary_table = Table(summary_data, colWidths=[80*mm, 40*mm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0), PURPLE),
            ('SPAN',        (0,0), (-1,0)),
            ('FONTSIZE',    (0,0), (-1,-1), 9),
            ('PADDING',     (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-2),
                [colors.white, GRAY_LIGHT] * 10),
            ('BACKGROUND',  (0,-3), (-1,-3), PURPLE_LIGHT),
            ('BACKGROUND',  (0,-2), (-1,-2), colors.HexColor('#FEE2E2')),
            ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('ALIGN',       (1,1), (-1,-1), 'RIGHT'),
        ]))

        # Push summary to right side
        wrapper = Table([[None, summary_table]],
                        colWidths=[45*mm, 120*mm])
        wrapper.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(wrapper)
        story.append(Spacer(1, 8*mm))

        # ── FOOTER ────────────────────────────────────
        story.append(HRFlowable(width='100%', color=PURPLE_LIGHT))
        story.append(Spacer(1, 3*mm))

        notes = billing_data.get('notes', '')
        if notes:
            story.append(Paragraph(f"<b>Notes:</b> {notes}", small_style))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph(
            'Thank you for choosing Event Planner Pro! '
            'This is a computer-generated invoice.',
            make_style('Footer', fontSize=8, textColor=GRAY,
                       alignment=TA_CENTER)
        ))

        # ── Build PDF ─────────────────────────────────
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        return None