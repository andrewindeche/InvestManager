from django.contrib import admin
from .models import Account,AccountPermissions

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    """
    Register name and users fields to admin
    """
    def get_queryset(self, request):
        """
        Method to filter staff and non-staff users
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(users=request.user)
    
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('users',)
    
    exclude = ['balance']
admin.site.register(AccountPermissions)
admin.site.register(Account,AccountAdmin)
