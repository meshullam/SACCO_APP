from django.contrib import admin
from .models import Loan
from .models import Savings

admin.site.register(Loan)
admin.site.register(Savings)
