from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'last_login', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('username',)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
