from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from api.models import *


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'last_login', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('username',)


class MaskInline(admin.StackedInline):
    model = ResultGroupMask
    extra = 0


@admin.register(ResultGroupNew)
class ResultGroupNewAdmin(admin.ModelAdmin):
    list_display = ('name', 'alt_name', 'category')
    ordering = ('name',)
    search_fields = ('name', 'alt_name', 'category')
    inlines = [MaskInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
