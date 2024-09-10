from django.contrib import admin
from .models import User,Account,AccountPermissions
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.register(Account)
admin.site.register(AccountPermissions)
