from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

class MainUser(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="My Portfolio")
    description = models.TextField(blank=True, null=True)
    initialInvestment = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    cashBalance = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    riskTolerance = models.CharField(max_length=10, choices=RISK_CHOICES, default='Medium')
    investmentGoal = models.CharField(max_length=100, default="Long-term growth")
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"


class Transaction(models.Model):
    TRANSACTION_CHOICES = [
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
    ]
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    stockSymbol = models.CharField(max_length=10)
    stockName = models.CharField(max_length=100)
    transactionType = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    quantity = models.IntegerField()
    pricePerShare = models.DecimalField(max_digits=12, decimal_places=2)
    totalPrice = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transactionType} {self.stockSymbol} ({self.quantity})"

    @staticmethod
    def getOwnedShares(portfolio, stockSymbol):
        """Return the number of shares owned for a given stock."""
        bought = sum(t.quantity for t in Transaction.objects.filter(
            portfolio=portfolio,
            stockSymbol=stockSymbol,
            transactionType="Buy"
        ))
        sold = sum(t.quantity for t in Transaction.objects.filter(
            portfolio=portfolio,
            stockSymbol=stockSymbol,
            transactionType="Sell"
        ))
        return bought - sold
