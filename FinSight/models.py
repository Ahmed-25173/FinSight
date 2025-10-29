from django.db import models
from django.contrib.auth.models import AbstractUser

class MainUser(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    country = models.CharField(max_length=50, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
