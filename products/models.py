from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

        
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )
    # CATEGORY_CHOICES = [
    #     ("restaurant", "Restaurant"),
    #     ("bar", "Bar"),
    #     ("boutique", "Boutique"),
    # ]
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def profit_margin(self):
        if self.selling_price and self.purchase_price:
            return self.selling_price - self.purchase_price
        return 0

    @property
    def marge_total(self):
        return self.stock * self.profit_margin

    @property
    def stock_value(self):
        return self.stock * self.purchase_price
    
    def __str__(self):
        return self.name