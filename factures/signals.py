from django.db.models.signals import post_save
from django.dispatch import receiver

from sales.models import Sale
from factures.models import Facture


@receiver(post_save, sender=Sale)
def create_facture(sender, instance, created, **kwargs):
    if created:
        Facture.objects.create(
            sale=instance,
            customer=instance.customer,
            total=instance.total_amount
        )