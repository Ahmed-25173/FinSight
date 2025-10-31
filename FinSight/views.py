from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import MainUser
from .models import Portfolio




@login_required
def Home(request):
    return render(request,'home.html')






def userSignup(request):
    if request.method == "POST":
        data = request.POST
        fname = data.get('firstname')
        number = data.get('number')
        country = data.get('country')
        balance = data.get('balance')
        uname = data.get('username')
        email = data.get('email')
        password1 = data.get('password1')
        password2 = data.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if MainUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('signup')

        if MainUser.objects.filter(username=uname).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        user = MainUser.objects.create_user(
            username=uname,
            email=email,
            password=password1,
            name=fname,
            number=number,
            country=country,
            balance=balance
        )
        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('login')

    return render(request, 'signup.html')




def Login(request):
    if request.method == "POST":
        data = request.POST
        email = data.get('email')
        password = data.get('password')

        try:
            user = MainUser.objects.get(email=email)
        except MainUser.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('login')

        auth = authenticate(request, username=email, password=password)
        if auth is None:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

        
        login(request, auth)
        return redirect('home')
        

    return render(request, 'login.html')






def logoutView(request):
    logout(request)
    return redirect('home')



@login_required
def update_profile(request):
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
        portfolio.currentValue = request.POST.get('currentValue')
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








