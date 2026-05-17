from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Paiement


@receiver(post_save, sender=Paiement)
def update_facture_payment(sender, instance, **kwargs):
    facture = instance.facture

    facture.amount_paid += instance.montant
    facture.update_status()