from django.db import models
from decimal import Decimal

# Create your models here.
class ShopSettings(models.Model):
    DEVISE_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('CDF', 'CDF'),
        ('BIF', 'BIF'),
    ]
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    currency = models.CharField(
        max_length=10,
        choices=DEVISE_CHOICES,
        default='BIF'
    )
    tva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    logo = models.ImageField(upload_to="logo/", blank=True, null=True)

    def __str__(self):
    	return self.name