from django.db import models
from products.models import Product
from suppliers.models import Supplier
from django.contrib.auth.models import User, Group

# Create your models here.
class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # qui a ajouté le stock

    def save(self, *args, **kwargs):
        # Ajouter automatiquement au stock du produit
        if not self.pk:  # uniquement à la création
            self.product.stock += self.quantity
            self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} – {self.quantity}"
