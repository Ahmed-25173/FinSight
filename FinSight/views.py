from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import MainUser, Portfolio, Transaction, StockPriceCache, FavoriteStock
from decimal import Decimal
import csv
from django.http import HttpResponse
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_POST

# ----------------------------
# AUTHENTICATION VIEWS
# ----------------------------
@login_required
def home(request):
    return render(request, 'home.html')


def userSignup(request):
    if request.method == "POST":
        data = request.POST
        firstName = data.get('firstname')
        number = data.get('number')
        country = data.get('country')
        balance = Decimal(data.get('balance') or 10000)
        userName = data.get('username')
        email = data.get('email')
        password1 = data.get('password1')
        password2 = data.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if MainUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('signup')

        if MainUser.objects.filter(username=userName).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        MainUser.objects.create_user(
            username=userName,
            email=email,
            password=password1,
            name=firstName,
            number=number,
            country=country,
            balance=balance
        )
        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('login')

    return render(request, 'signup.html')


def loginView(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid email or password.')
        return redirect('login')

    return render(request, 'login.html')


def logoutView(request):
    logout(request)
    return redirect('home')


# ----------------------------
# USER PROFILE
# ----------------------------
@login_required
def updateProfile(request):
    user = request.user
    if request.method == "POST":
        number = request.POST.get('number')
        balance = request.POST.get('balance')
        country = request.POST.get('country')

        user.number = number
        user.balance = Decimal(balance) if balance else Decimal(0)
        user.country = country
        user.save()

        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('update_profile')

    return render(request, 'update_profile.html', {'user': user})



@login_required
def createPortfolio(request):
    if hasattr(request.user, 'portfolio'):
        messages.warning(request, "You already have a portfolio.")
        return redirect('viewPortfolio')

    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        cashBalance = Decimal(request.POST.get('cashBalance') or 10000)
        riskTolerance = request.POST.get('riskTolerance')
        investmentGoal = request.POST.get('investmentGoal')

        Portfolio.objects.create(
            user=request.user,
            name=name,
            description=description,
            cashBalance=cashBalance,
            riskTolerance=riskTolerance,
            investmentGoal=investmentGoal
        )
        messages.success(request, "Portfolio created successfully!")
        return redirect('viewPortfolio')

    return render(request, 'createPortfolio.html')

from django.core.cache import cache
from decimal import Decimal
from .models import StockPriceCache
import yfinance as yf
from django.utils import timezone

CACHE_TIMEOUT = 3600  # seconds = 1 hour

def get_stock_price(symbol):
    """
    Get stock price from cache or fetch live if missing.
    Updates the database cache as well.
    Returns tuple: (price: Decimal, last_updated: datetime)
    """
    cache_key = f"stock_price_{symbol}"
    cached = cache.get(cache_key)

    if cached:
        return cached  # (price, last_updated)

    # Fetch live price
    try:
        stock = yf.Ticker(symbol)
        live_price = stock.info.get('regularMarketPrice')
        if live_price is None:
            # fallback to database cache
            db_cache = StockPriceCache.objects.filter(ticker=symbol).first()
            if db_cache:
                result = (Decimal(db_cache.last_price), db_cache.last_updated)
                cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
                return result
            return (Decimal(0), None)

        live_price_decimal = Decimal(str(live_price))

        # Update database cache
        db_cache, _ = StockPriceCache.objects.get_or_create(ticker=symbol)
        db_cache.last_price = live_price_decimal
        db_cache.last_updated = timezone.now()
        db_cache.save()

        # Update Django cache
        result = (live_price_decimal, db_cache.last_updated)
        cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
        return result
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return (Decimal(0), None)




@login_required
def viewPortfolio(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    diversification = portfolio.diversification or {}
    stock_data = []
    total_portfolio_value = Decimal(0)
    total_portfolio_pnl = Decimal(0)
    last_cache_time = None

    favorite_symbols = set(FavoriteStock.objects.filter(user=request.user)
                           .values_list('symbol', flat=True))

    for symbol, percent in diversification.items():
        owned_qty = Transaction.getOwnedShares(portfolio, symbol)

        current_price, updated_at = get_stock_price(symbol)

        if updated_at and (not last_cache_time or updated_at > last_cache_time):
            last_cache_time = updated_at

        avg_buy_price = Transaction.getAverageBuyPrice(portfolio, symbol)
        holding_value = owned_qty * current_price
        pnl = owned_qty * (current_price - avg_buy_price)

        total_portfolio_value += holding_value
        total_portfolio_pnl += pnl

        stock_data.append({
            'symbol': symbol,
            'owned_qty': owned_qty,
            'current_price': round(current_price, 2),
            'avg_buy_price': round(avg_buy_price, 2),
            'holding_value': round(holding_value, 2),
            'pnl': round(pnl, 2),
            'percent': percent
        })

    # Compute top 5 holdings by value
    sorted_by_value = sorted(stock_data, key=lambda x: x['holding_value'], reverse=True)
    top5 = sorted_by_value[:5]
    top5_with_value_pct = []

    for item in top5:
        pct_by_value = (Decimal(item['holding_value']) / total_portfolio_value * 100) if total_portfolio_value > 0 else Decimal(0)
        top5_with_value_pct.append({
            'symbol': item['symbol'],
            'qty': item['owned_qty'],
            'price': item['current_price'],
            'value': item['holding_value'],
            'pnl': item['pnl'],
            'avg_buy_price': item['avg_buy_price'],
            'percent_by_diversification': item['percent'],
            'percent_by_value': round(pct_by_value, 2)
        })

    context = {
        'portfolio': portfolio,
        'diversification': diversification,
        'stock_data': stock_data,
        'total_portfolio_value': round(total_portfolio_value, 2),
        'total_portfolio_pnl': round(total_portfolio_pnl, 2),
        'last_cache_time': last_cache_time,
        'top5': top5_with_value_pct,
        'favorite_symbols': favorite_symbols,
    }

    return render(request, 'viewPortfolio.html', context)




@login_required
def updatePortfolio(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    if request.method == "POST":
        portfolio.name = request.POST.get('name')
        portfolio.description = request.POST.get('description')
        portfolio.initialInvestment = Decimal(request.POST.get('initialInvestment') or portfolio.cashBalance)
        portfolio.cashBalance = Decimal(request.POST.get('cashBalance') or portfolio.cashBalance)
        portfolio.riskTolerance = request.POST.get('riskTolerance')
        portfolio.investmentGoal = request.POST.get('investmentGoal')
        portfolio.save()
        messages.success(request, "Portfolio updated successfully!")
        return redirect('viewPortfolio')

    return render(request, 'updatePortfolio.html', {'portfolio': portfolio})


@login_required
def deletePortfolio(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    if request.method == "POST":
        portfolio.delete()
        messages.success(request, "Portfolio deleted successfully!")
        return redirect('home')
    return render(request, 'deletePortfolio.html', {'portfolio': portfolio})





@login_required
def addTransaction(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)

    if request.method == "POST":
        stockSymbol = request.POST.get('stockSymbol').upper()
        stockName = request.POST.get('stockName')
        transactionType = request.POST.get('transactionType')
        shareQuant = int(request.POST.get('quantity'))
        note = request.POST.get('note', '')

        # Get latest price using the new caching function
        pricePerShare, last_updated = get_stock_price(stockSymbol)

        if pricePerShare == 0:
            messages.error(request, f"Could not fetch price for {stockSymbol}.")
            return redirect('addTransaction')

        totalPrice = shareQuant * Decimal(pricePerShare)

        # Validate Sell transaction
        if transactionType == "Sell":
            ownedShares = Transaction.getOwnedShares(portfolio, stockSymbol)
            if ownedShares <= 0 or shareQuant > ownedShares:
                messages.error(
                    request,
                    f"Cannot sell {shareQuant} shares of {stockSymbol}. You own {ownedShares}."
                )
                return redirect('addTransaction')

        # Validate Buy transaction
        elif transactionType == "Buy":
            if totalPrice > portfolio.cashBalance:
                messages.error(
                    request,
                    f"Insufficient cash balance to buy {shareQuant} shares of {stockSymbol}."
                )
                return redirect('addTransaction')

        # Create transaction
        Transaction.objects.create(
            portfolio=portfolio,
            stockSymbol=stockSymbol,
            stockName=stockName,
            transactionType=transactionType,
            quantity=shareQuant,
            pricePerShare=Decimal(pricePerShare),
            totalPrice=totalPrice,
            note=note
        )

        # Update portfolio cash balance
        portfolio.cashBalance += -totalPrice if transactionType == "Buy" else totalPrice
        portfolio.save()

        messages.success(request, f"{transactionType} transaction for {stockSymbol} added successfully.")
        return redirect('viewTransactions')

    return render(request, 'addTransaction.html', {'portfolio': portfolio})






@login_required
def viewTransactions(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-date')

    transaction_type = request.GET.get('type')
    stock_symbol = request.GET.get('symbol')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    if transaction_type and transaction_type != "All":
        transactions = transactions.filter(transactionType=transaction_type)
    if stock_symbol:
        transactions = transactions.filter(stockSymbol__icontains=stock_symbol)
    if start_date:
        transactions = transactions.filter(date__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__date__lte=end_date)

    context = {
        'transactions': transactions,
        'selected_type': transaction_type or "All",
        'symbol': stock_symbol or "",
        'start_date': start_date or "",
        'end_date': end_date or "",
    }

    return render(request, 'viewTransactions.html', context)


@login_required
def updateTransaction(request, id):
    transaction = get_object_or_404(Transaction, id=id, portfolio__user=request.user)
    if request.method == "POST":
        transaction.stockSymbol = request.POST.get('stockSymbol').upper()
        transaction.stockName = request.POST.get('stockName')
        transaction.transactionType = request.POST.get('transactionType')
        transaction.quantity = int(request.POST.get('quantity'))
        transaction.pricePerShare = Decimal(request.POST.get('pricePerShare'))
        transaction.note = request.POST.get('note', '')
        transaction.totalPrice = transaction.quantity * transaction.pricePerShare
        transaction.save()
        messages.success(request, "Transaction updated successfully!")
        return redirect('viewTransactions')
    return render(request, 'updateTransaction.html', {'transaction': transaction})


@login_required
def deleteTransaction(request, id):
    transaction = get_object_or_404(Transaction, id=id, portfolio__user=request.user)
    if request.method == "POST":
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
        return redirect('viewTransactions')
    return render(request, 'deleteTransaction.html', {'transaction': transaction})


@login_required
def downloadTransactionsCSV(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-date')

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="transaction_history.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Date", "Stock Symbol", "Stock Name", "Transaction Type",
        "Quantity", "Price Per Share", "Total Price", "Note"
    ])

    for t in transactions:
        writer.writerow([
            t.date.strftime("%Y-%m-%d %H:%M"),
            t.stockSymbol,
            t.stockName,
            t.transactionType,
            t.quantity,
            float(t.pricePerShare),
            float(t.totalPrice),
            t.note or ""
        ])

    return response


@login_required
def favoriteStocksPage(request):
    """
    Show the user's favorite stocks with cached or live prices.
    """
    favorites = FavoriteStock.objects.filter(user=request.user).order_by('-added_at')
    stock_data = []
    last_cache_time = None
    cache_expiry = timedelta(hours=12)
    total_value = Decimal(0)

    for fav in favorites:
        symbol = fav.symbol
        name = fav.name or ""
        current_price = Decimal(0)
        cache = StockPriceCache.objects.filter(ticker=symbol).first()
        need_update = True if not cache else timezone.now() - cache.last_updated > cache_expiry

        if cache:
            current_price = Decimal(cache.last_price)
            if not last_cache_time or cache.last_updated > last_cache_time:
                last_cache_time = cache.last_updated

        if need_update:
            live_price = fetch_and_update_stock_price(symbol)
            if live_price is not None:
                current_price = Decimal(live_price)
                cache = StockPriceCache.objects.get(ticker=symbol)
                if not last_cache_time or cache.last_updated > last_cache_time:
                    last_cache_time = cache.last_updated

        # optional: compute user's owned shares in portfolio(s) for this symbol
        # We'll sum across all portfolios the user owns (if any)
        owned_qty = 0
        # If user has a portfolio we use it; otherwise 0
        try:
            portfolio = request.user.portfolio
            owned_qty = Transaction.getOwnedShares(portfolio, symbol)
        except Portfolio.DoesNotExist:
            owned_qty = 0

        value = owned_qty * current_price
        total_value += Decimal(value)

        stock_data.append({
            'symbol': symbol,
            'name': name,
            'current_price': round(current_price, 2),
            'owned_qty': owned_qty,
            'value': round(value, 2),
        })

    context = {
        'favorites': favorites,
        'stock_data': stock_data,
        'last_cache_time': last_cache_time,
        'total_value': round(total_value, 2),
    }
    return render(request, 'favorite_stocks.html', context)

@require_POST
@login_required
def addFavoriteStock(request):
    """
    Add a symbol to the user's favorites. Expects POST with 'symbol' and optional 'name'.
    """
    symbol = request.POST.get('symbol', '').upper().strip()
    name = request.POST.get('name', '').strip()
    if not symbol:
        messages.error(request, "No symbol provided.")
        return redirect(request.META.get('HTTP_REFERER', 'favoriteStocksPage'))

    fav, created = FavoriteStock.objects.get_or_create(user=request.user, symbol=symbol, defaults={'name': name})
    if created:
        messages.success(request, f"{symbol} added to your favorites.")
    else:
        messages.info(request, f"{symbol} is already in your favorites.")
    return redirect(request.META.get('HTTP_REFERER', 'favoriteStocksPage'))

@require_POST
@login_required
def removeFavoriteStock(request):
    """
    Remove a symbol from the user's favorites. Expects POST with 'symbol'.
    """
    symbol = request.POST.get('symbol', '').upper().strip()
    if not symbol:
        messages.error(request, "No symbol provided.")
        return redirect(request.META.get('HTTP_REFERER', 'favoriteStocksPage'))

    deleted, _ = FavoriteStock.objects.filter(user=request.user, symbol=symbol).delete()
    if deleted:
        messages.success(request, f"{symbol} removed from favorites.")
    else:
        messages.info(request, f"{symbol} wasn't in your favorites.")
    return redirect(request.META.get('HTTP_REFERER', 'favoriteStocksPage'))

from decimal import Decimal
from .models import StockPriceCache


