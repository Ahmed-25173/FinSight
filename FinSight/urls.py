from django.urls import path
from .views import userSignup,Login,logoutView, Home
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', Home, name = 'home'),
    path('signup/', userSignup, name="signup"),
    path('login/', Login, name="login"),
    path('logout/', logoutView, name='logout'),
    path('passwordchange/', auth_views.PasswordChangeView.as_view(template_name='ChangePassword.html'), name='changepassword'),
    path('passwordchangedone/', auth_views.PasswordChangeDoneView.as_view(template_name='PasswordChangeDone.html'), name='password_change_done'),

    ]
