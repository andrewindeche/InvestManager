from django.contrib import admin
from .models import User,Account,AccountPermissions
from django.contrib.auth.admin import UserAdmin

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('users',)
admin.site.register(AccountPermissions)
admin.site.register(Account,AccountAdmin)
