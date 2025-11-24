from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.userSignup, name='signup'),
    path('signup/', views.userSignup, name='signup'),
    path('login/', views.loginView, name='login'),
    path('logout/', views.logoutView, name='logout'),
    path('home/', views.home, name='home'),
    path('update-profile/', views.updateProfile, name='update_profile'),
    path('passwordchange/', auth_views.PasswordChangeView.as_view(template_name='ChangePassword.html'), name='changepassword'),
    path('passwordchangedone/', auth_views.PasswordChangeDoneView.as_view(template_name='PasswordChangeDone.html'), name='password_change_done'),
    path('create/', views.createPortfolio, name='createPortfolio'),
    path('view/', views.viewPortfolio, name='viewPortfolio'),
    path('update/', views.updatePortfolio, name='updatePortfolio'),
    path('delete/', views.deletePortfolio, name='deletePortfolio'),
    path('transactions/add/', views.addTransaction, name='addTransaction'),
    path('transactions/view/', views.viewTransactions, name='viewTransactions'),
    path('transactions/update/<int:id>/', views.updateTransaction, name='updateTransaction'),
    path('transactions/delete/<int:id>/', views.deleteTransaction, name='deleteTransaction'),
    path('transactions/download-csv/', views.downloadTransactionsCSV, name='downloadTransactionsCSV'),
    path('favorite-stocks/', views.favoriteStocksPage, name='favoriteStocksPage'),
    path('favorite-stocks/add/', views.addFavoriteStock, name='addFavoriteStock'),
    path('favorite-stocks/remove/', views.removeFavoriteStock, name='removeFavoriteStock'),



]




  