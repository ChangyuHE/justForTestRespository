from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from api.models import *


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'last_login', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('username',)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Component)
admin.site.register(Env)
admin.site.register(Generation)
admin.site.register(Platform)
admin.site.register(Os)
admin.site.register(Status)

admin.site.register(Milestone)
