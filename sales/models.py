from django.db import models
from django.contrib.auth.models import User, Group
from decimal import Decimal

from products.models import Product

# Create your models here.
class Sale(models.Model):
    STATUS_CHOICES = [
        ('draft', 'En cours'),
        ('completed', 'Finalisée'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    customer_name = models.CharField(max_length=80, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Vente #{self.id}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    @property
    def total_price(self):
        return self.quantity * self.selling_price

    @property
    def profit(self):
        return (self.selling_price - self.purchase_price) * self.quantity

    
    def save(self, *args, **kwargs):
        if not self.pk:  # seulement si création
            if self.quantity > self.product.stock:
                raise ValueError("Stock insuffisant")

            self.product.stock -= self.quantity
            self.product.save()

        super().save(*args, **kwargs)

        # Recalculer la vente
        sale = self.sale
        sale.total_amount = sum(item.total_price for item in sale.items.all())
        sale.total_profit = sum(item.profit for item in sale.items.all())
        sale.save()

    
    def delete(self, *args, **kwargs):

        # Remettre le stock
        self.product.stock += self.quantity
        self.product.save()

        super().delete(*args, **kwargs)

        # Recalculer la vente
        sale = self.sale
        sale.total_amount = sum(item.total_price for item in sale.items.all())
        sale.total_profit = sum(item.profit for item in sale.items.all())
        sale.save()

    def __str__(self):
        return str(self.product)