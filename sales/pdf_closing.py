from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import date

from core.models import ShopSettings
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Sum

from sales.models import Sale
from factures.models import Facture  


def generate_closing_pdf(user, target_date=None):

    shop = ShopSettings.objects.first()

    if target_date is None:
        target_date = date.today()

    # =========================================
    # ROLE BASED SALES
    # =========================================
    if user.groups.filter(name="Admin").exists():

        sales = Sale.objects.filter(
            status="completed",
            created_at__date=target_date
        )

        title_role = "ADMIN - RAPPORT GLOBAL"

    else:

        sales = Sale.objects.filter(
            status="completed",
            created_at__date=target_date,
            user=user
        )

        title_role = "CAISSE - RAPPORT PERSONNEL"

    # =========================================
    # STATS SALES (OPTIMISÉ)
    # =========================================
    total_sales = sales.count()

    total_amount = sales.aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    total_profit = sales.aggregate(
        total=Sum('total_profit')
    )['total'] or 0

    # =========================================
    # CREDIT DU JOUR (FACTURES)
    # =========================================
    credits = Facture.objects.filter(
        created_at__date=target_date,
        status__in=['issued', 'partial']
    ).select_related('customer')

    total_credit = sum(
        f.remaining for f in credits
    )

    # =========================================
    # PDF INIT
    # =========================================
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    # =========================================
    # TITLE
    # =========================================
    title = Paragraph(
        f"<b>{title_role}</b><br/>Date: {target_date}",
        styles["Title"]
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    # =========================================
    # USER INFO
    # =========================================
    user_info = Paragraph(
        f"Utilisateur : <b>{user.username}</b>",
        styles["Normal"]
    )
    elements.append(user_info)
    elements.append(Spacer(1, 10))

    # =========================================
    # SUMMARY TABLE
    # =========================================
    summary_data = [
        ["Nombre de ventes", total_sales],
        ["Chiffre d'affaires", f"{intcomma(total_amount)} {shop.currency}"],
        ["Bénéfice total", f"{intcomma(total_profit)} {shop.currency}"],
    ]

    table = Table(summary_data, colWidths=[250, 200])

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # =========================================
    # SALES TABLE
    # =========================================
    elements.append(
        Paragraph("<b>DÉTAIL DES VENTES</b>", styles["Heading2"])
    )

    sales_data = [["ID", "Client", "User", "Total", "Profit"]]

    for s in sales:

        sales_data.append([
            str(s.id),
            s.customer.full_name if s.customer else "-",
            s.user.username if s.user else "-",
            f"{intcomma(s.total_amount)} {shop.currency}",
            f"{intcomma(s.total_profit)} {shop.currency}",
        ])

    sales_table = Table(
        sales_data,
        colWidths=[50, 150, 100, 100, 100]
    )

    sales_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ]))

    elements.append(sales_table)
    elements.append(Spacer(1, 20))

    # =========================================
    # CREDIT SECTION
    # =========================================
    elements.append(
        Paragraph("<b>CRÉDIT ACCORDÉ AUJOURD'HUI</b>", styles["Heading2"])
    )

    credit_summary = [
        ["Total crédit (reste à payer)", f"{intcomma(total_credit)} {shop.currency}"],
        ["Nombre de crédits", len(credits)],
    ]

    credit_table = Table(credit_summary, colWidths=[250, 200])

    credit_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ffdddd")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(credit_table)
    elements.append(Spacer(1, 15))

    # =========================================
    # CREDIT DETAIL
    # =========================================
    elements.append(
        Paragraph("<b>Détail des crédits</b>", styles["Heading3"])
    )

    credit_data = [["Facture", "Client", "Total", "Payé", "Reste"]]

    for f in credits:

        credit_data.append([
            f.reference,
            f.customer.full_name if f.customer else "-",
            f"{intcomma(f.total)} {shop.currency}",
            f"{intcomma(f.amount_paid)} {shop.currency}",
            f"{intcomma(f.remaining)} {shop.currency}",
        ])

    credit_table_detail = Table(
        credit_data,
        colWidths=[80, 120, 100, 100, 100]
    )

    credit_table_detail.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ffe5e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
    ]))

    elements.append(credit_table_detail)
    elements.append(Spacer(1, 20))

    # =========================================
    # FOOTER
    # =========================================
    footer = Paragraph(
        "<i>Clôture générée automatiquement par le système ERP</i>",
        styles["Italic"]
    )

    elements.append(footer)

    doc.build(elements)

    buffer.seek(0)
    return buffer