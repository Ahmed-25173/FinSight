from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


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


class Portfolio(models.Model):
    RISK_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    initialInvestment = models.DecimalField(max_digits=12, decimal_places=2)
    cashBalance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    riskTolerance = models.CharField(max_length=10, choices=RISK_CHOICES)
    investmentGoal = models.CharField(max_length=100)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"
