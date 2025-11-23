from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import JSONField
from decimal import Decimal

class MainUser(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'))
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
    cashBalance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'))
    riskTolerance = models.CharField(max_length=10, choices=RISK_CHOICES, default='Medium')
    investmentGoal = models.CharField(max_length=100, default="Long-term growth")
    createdAt = models.DateTimeField(auto_now_add=True)
    diversification = JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

    def update_diversification(self):
        transactions = Transaction.objects.filter(portfolio=self)
        stock_totals = {}
        for t in transactions:
            symbol = t.stockSymbol
            qty = t.quantity if t.transactionType == "Buy" else -t.quantity
            stock_totals[symbol] = stock_totals.get(symbol, 0) + qty
        stock_totals = {k: v for k, v in stock_totals.items() if v > 0}
        total_shares = sum(stock_totals.values())
        if total_shares == 0:
            self.diversification = {}
        else:
            self.diversification = {k: round((v / total_shares) * 100, 2) for k, v in stock_totals.items()}
        self.save()

    def total_holdings_value(self):
        total = Decimal(0)
        for symbol, _ in self.diversification.items():
            cache = StockPriceCache.objects.filter(ticker=symbol).first()
            if cache:
                qty = Transaction.getOwnedShares(self, symbol)
                total += Decimal(qty) * Decimal(cache.last_price)
        return total

    def total_profit_loss(self):
        total_pnl = Decimal(0)
        for symbol, _ in self.diversification.items():
            cache = StockPriceCache.objects.filter(ticker=symbol).first()
            if cache:
                qty = Transaction.getOwnedShares(self, symbol)
                avg_buy_price = Transaction.getAverageBuyPrice(self, symbol)
                total_pnl += Decimal(qty) * (Decimal(cache.last_price) - Decimal(avg_buy_price))
        return total_pnl

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

    @staticmethod
    def getAverageBuyPrice(portfolio, stockSymbol):
        buys = Transaction.objects.filter(
            portfolio=portfolio,
            stockSymbol=stockSymbol,
            transactionType="Buy"
        )
        total_qty = sum(t.quantity for t in buys)
        if total_qty == 0:
            return Decimal(0)
        total_spent = sum(Decimal(t.pricePerShare) * t.quantity for t in buys)
        return total_spent / total_qty

@receiver(post_save, sender=Transaction)
@receiver(post_delete, sender=Transaction)
def update_portfolio_diversification(sender, instance, **kwargs):
    instance.portfolio.update_diversification()

class StockPriceCache(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    last_price = models.DecimalField(max_digits=12, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ticker}: {self.last_price}"
