from django.db import models
from customers.models import Customer

class RestaurantTable(models.Model):
    STATUS_CHOICES = [
        ("free", "Libre"),
        ("occupied", "Occupée"),
        ("reserved", "Réservée"),
    ]
    name = models.CharField(max_length=50)
    capacity = models.IntegerField(default=4)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="free"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    def __str__(self):
        return self.name