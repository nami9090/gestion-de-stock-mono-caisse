from django.db import models


class Customer(models.Model):
    full_name = models.CharField(max_length=150)
    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    email = models.EmailField(
        blank=True,
        null=True
    )
    address = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.full_name