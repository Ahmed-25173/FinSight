from django.contrib import admin
from .models import MainUser, Portfolio, Transaction

admin.site.register(MainUser)
admin.site.register(Portfolio)
admin.site.register(Transaction)
