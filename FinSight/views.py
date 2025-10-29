from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import MainUser



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

        user = MainUser.objects.create_user(username=uname, email=email, password=password1 ,name = fname,number = number,country = country, balance = balance )
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
        return redirect('')
        

    return render(request, 'login.html')






def logoutView(request):
    logout(request)
    return redirect('home')