from django.db.models import Sum, Count
from datetime import date
from .models import Sale
from accounts.permission import is_admin, is_caisse


def closing_report(user, target_date=None):

    if target_date is None:
        target_date = date.today()

    # ADMIN = toutes les ventes
    if is_admin(user):
        sales = Sale.objects.filter(
            status="completed",
            created_at__date=target_date
        )
    else:
        # CAISSE = seulement ses ventes
        sales = Sale.objects.filter(
            status="completed",
            created_at__date=target_date,
            user=user
        )

    summary = sales.aggregate(
        total_sales=Count("id"),
        total_amount=Sum("total_amount"),
        total_profit=Sum("total_profit"),
    )

    return {
        "date": target_date,
        "sales": sales,
        "total_sales": summary["total_sales"] or 0,
        "total_amount": summary["total_amount"] or 0,
        "total_profit": summary["total_profit"] or 0,
        "is_admin_view": is_admin(user)
    }