from django.urls import path
from .views import userSignup, Login, logoutView, Home
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', userSignup, name='signup'),  
    path('signup/', userSignup, name="signup"),
    path('login/', Login, name="login"),
    path('logout/', logoutView, name='logout'),
    path('home/', Home, name='home'), 
    path('passwordchange/', auth_views.PasswordChangeView.as_view(template_name='ChangePassword.html'), name='changepassword'),
    path('passwordchangedone/', auth_views.PasswordChangeDoneView.as_view(template_name='PasswordChangeDone.html'), name='password_change_done'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('create/', views.createPortfolio, name='createPortfolio'),
    path('view/', views.viewPortfolio, name='viewPortfolio'),
    path('update/', views.updatePortfolio, name='updatePortfolio'),
    path('delete/', views.deletePortfolio, name='deletePortfolio'),
]
