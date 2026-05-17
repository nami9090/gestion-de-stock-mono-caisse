from django.db import models
from django.utils import timezone

from sales.models import Sale
from customers.models import Customer


class Facture(models.Model):

    STATUT_CHOICES = [
        ('draft', 'Brouillon'),
        ('issued', 'Émise'),
        ('partial', 'Partiellement payée'),
        ('paid', 'Payée'),
        ('canceled', 'Annulée'),
    ]

    reference = models.CharField(
        max_length=30,
        unique=True,
        blank=True
    )

    sale = models.OneToOneField(
        Sale,
        on_delete=models.CASCADE,
        related_name='facture'
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='draft'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================
    # GENERATE UNIQUE REFERENCE
    # =====================================
    @staticmethod
    def generate_reference():

        year = timezone.now().year

        last_facture = Facture.objects.order_by('-id').first()

        if last_facture:
            next_id = last_facture.id + 1
        else:
            next_id = 1

        reference = f"FAC-{year}-{next_id:05d}"

        # sécurité anti collision
        while Facture.objects.filter(reference=reference).exists():

            next_id += 1
            reference = f"FAC-{year}-{next_id:05d}"

        return reference

    # =====================================
    # SAVE
    # =====================================
    def save(self, *args, **kwargs):

        if not self.reference:
            self.reference = self.generate_reference()

        super().save(*args, **kwargs)

    # =====================================
    # REMAINING
    # =====================================
    @property
    def remaining(self):
        return self.total - self.amount_paid

    # =====================================
    # UPDATE STATUS
    # =====================================
    def update_status(self):

        if self.amount_paid <= 0:
            self.status = 'issued'

        elif self.amount_paid < self.total:
            self.status = 'partial'

        else:
            self.status = 'paid'

    # =====================================
    # RECALCULATE PAYMENTS
    # =====================================
    def recalc_payments(self):

        self.amount_paid = sum(
            p.montant for p in self.paiements.all()
        )

        self.update_status()

        self.save()

    def __str__(self):
        return self.reference