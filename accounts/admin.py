from django.contrib import admin
from .models import Account,AccountPermissions

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    """
    Register name and users fields to admin
    """
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('users',)
admin.site.register(AccountPermissions)
admin.site.register(Account,AccountAdmin)
