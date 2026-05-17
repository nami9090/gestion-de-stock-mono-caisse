from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import date
from core.models import ShopSettings
from django.contrib.humanize.templatetags.humanize import intcomma
from .models import Sale


def generate_closing_pdf(user, target_date=None):
    shop = ShopSettings.objects.first()
    if target_date is None:
        target_date = date.today()

    # LOGIQUE ROLE-BASED

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

    total_sales = sales.count()
    total_amount = sum(s.total_amount for s in sales)
    total_profit = sum(s.total_profit for s in sales)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    # TITRE
    title = Paragraph(
        f"<b>{title_role}</b><br/>Date: {target_date}",
        styles["Title"]
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    # USER INFO
    user_info = Paragraph(
        f"Utilisateur : <b>{user.username}</b>",
        styles["Normal"]
    )
    elements.append(user_info)
    elements.append(Spacer(1, 10))

    # RÉSUMÉ
    summary_data = [
        ["Nombre de ventes", total_sales],
        ["Chiffre d'affaires", f"{intcomma(total_amount)} {shop.currency}"],
        ["Bénéfice total", f"{intcomma(total_profit)} {shop.currency}"],
    ]

    table = Table(summary_data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # DÉTAIL VENTES
    elements.append(Paragraph("<b>Détail des ventes</b>", styles["Heading2"]))

    sales_data = [["ID", "Client", "User", "Total", "Profit"]]

    for s in sales:
        sales_data.append([
            str(s.id),
            s.customer.full_name or "-",
            s.user.username if s.user else "-",
            str(intcomma(s.total_amount) + " " + shop.currency),
            str(intcomma(s.total_profit) + " " + shop.currency),
        ])

    sales_table = Table(sales_data, colWidths=[50, 150, 100, 100, 100])
    sales_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ]))

    elements.append(sales_table)

    elements.append(Spacer(1, 20))

    footer = Paragraph(
        "<i>Clôture générée automatiquement par le système ERP</i>",
        styles["Italic"]
    )
    elements.append(footer)

    doc.build(elements)

    buffer.seek(0)
    return buffer