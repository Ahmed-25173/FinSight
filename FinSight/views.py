from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import MainUser, Portfolio, Transaction
from decimal import Decimal



@login_required
def home(request):
    return render(request, 'home.html')


def userSignup(request):
    if request.method == "POST":
        data = request.POST
        firstName = data.get('firstname')
        number = data.get('number')
        country = data.get('country')
        balance = data.get('balance')
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

        user = MainUser.objects.create_user(
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
        if user is not None:
            login(request, user) 
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    return render(request, 'login.html')




def logoutView(request):
    logout(request)
    return redirect('home')


@login_required
def updateProfile(request):
    user = request.user
    if request.method == 'POST':
        number = request.POST.get('number')
        balance = request.POST.get('balance')
        country = request.POST.get('country')

        user.number = number
        user.balance = balance if balance else 0
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
        initialInvestment = request.POST.get('initialInvestment')
        cashBalance = request.POST.get('cashBalance')
        riskTolerance = request.POST.get('riskTolerance')
        investmentGoal = request.POST.get('investmentGoal')

        Portfolio.objects.create(
            user=request.user,
            name=name,
            description=description,
            initialInvestment=initialInvestment,
            cashBalance=cashBalance,
            riskTolerance=riskTolerance,
            investmentGoal=investmentGoal
        )
        messages.success(request, "Portfolio created successfully!")
        return redirect('viewPortfolio')

    return render(request, 'createPortfolio.html')


@login_required
def viewPortfolio(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    return render(request, 'viewPortfolio.html', {'portfolio': portfolio})


@login_required
def updatePortfolio(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    if request.method == "POST":
        portfolio.name = request.POST.get('name')
        portfolio.description = request.POST.get('description')
        portfolio.initialInvestment = request.POST.get('initialInvestment')
        portfolio.cashBalance = request.POST.get('cashBalance')
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
        stockSymbol = request.POST.get('stockSymbol')
        stockName = request.POST.get('stockName')
        transactionType = request.POST.get('transactionType')
        shareQuant = int(request.POST.get('quantity'))
        pricePerShare = Decimal(request.POST.get('pricePerShare')) 
        note = request.POST.get('note', '')

        totalPrice = Decimal(shareQuant) * pricePerShare

    
        if transactionType == "Sell":
            ownedShares = Transaction.getOwnedShares(portfolio, stockSymbol)
            if ownedShares <= 0:
                messages.error(request, f"You don’t own any {stockSymbol} shares to sell.")
                return redirect('addTransaction')
            if shareQuant > ownedShares:
                messages.error(request, f"You can only sell up to {ownedShares} shares of {stockSymbol}.")
                return redirect('addTransaction')
        
        elif transactionType == "Buy":
            if totalPrice > portfolio.cashBalance:
                messages.error(request, f"Insufficient cash balance to buy {shareQuant} shares of {stockSymbol}.")
                return redirect('addTransaction')

        Transaction.objects.create(
            portfolio=portfolio,
            stockSymbol=stockSymbol,
            stockName=stockName,
            transactionType=transactionType,
            quantity=shareQuant,
            pricePerShare=pricePerShare,
            totalPrice=totalPrice,
            note=note
        )

        if transactionType == "Buy":
            portfolio.cashBalance -= totalPrice
        elif transactionType == "Sell":
            portfolio.cashBalance += totalPrice
        portfolio.save()

        messages.success(request, f"{transactionType} transaction for {stockSymbol} added successfully.")
        return redirect('viewTransactions')

    return render(request, 'addTransaction.html', {'portfolio': portfolio})









@login_required
def viewTransactions(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-date')
    return render(request, 'viewTransactions.html', {'transactions': transactions})


@login_required
def updateTransaction(request, id):
    transaction = get_object_or_404(Transaction, id=id, portfolio__user=request.user)
    if request.method == "POST":
        transaction.stockSymbol = request.POST.get('stockSymbol')
        transaction.stockName = request.POST.get('stockName')
        transaction.transactionType = request.POST.get('transactionType')
        transaction.quantity = int(request.POST.get('quantity'))
        transaction.pricePerShare = float(request.POST.get('pricePerShare'))
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
