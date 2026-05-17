from django.db import models
from django.utils import timezone

from factures.models import Facture


class Paiement(models.Model):

    MODE_PAIEMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Carte'),
        ('mobile_money', 'Mobile Money'),
        ('credit', 'Crédit'),
    ]

    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE,
        related_name='paiements'
    )

    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT_CHOICES
    )

    reference_transaction = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================
    # GENERATE TRANSACTION REFERENCE
    # =====================================
    @staticmethod
    def generate_reference():

        year = timezone.now().year

        last_payment = Paiement.objects.order_by('-id').first()

        if last_payment:
            next_id = last_payment.id + 1
        else:
            next_id = 1

        reference = f"PAY-{year}-{next_id:05d}"

        # sécurité anti collision
        while Paiement.objects.filter(
            reference_transaction=reference
        ).exists():

            next_id += 1
            reference = f"PAY-{year}-{next_id:05d}"

        return reference

    # =====================================
    # SAVE
    # =====================================
    def save(self, *args, **kwargs):

        if not self.reference_transaction:

            self.reference_transaction = (
                self.generate_reference()
            )

        super().save(*args, **kwargs)

    def __str__(self):

        return (
            f"{self.reference_transaction}"
            f" - {self.facture.reference}"
        )