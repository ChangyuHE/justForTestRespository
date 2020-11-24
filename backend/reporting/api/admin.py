from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from simple_history.admin import SimpleHistoryAdmin

from api.models import *


class CustomUserAdmin(UserAdmin):
    class ProfileInline(admin.TabularInline):
        model = Profile
        can_delete = False
        verbose_name_plural = 'Profile'

    inlines = (ProfileInline,)

    list_display = ('username', 'first_name', 'last_name', 'email', 'last_login', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('username',)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Component)
admin.site.register(Milestone)


@admin.register(Result)
class ResultAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'validation')
    ordering = ('id', 'validation')
    search_fields = ('id',)


@admin.register(Env)
class EnvAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name')
    ordering = ('name', 'short_name')
    search_fields = ('name', 'short_name')
    list_filter = ('short_name',)


@admin.register(Generation)
class GenerationAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'weight')
    ordering = ('name', 'parent', 'weight')
    search_fields = ('name', 'parent', 'weight')
    list_filter = ('parent', 'weight')


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'generation', 'aliases', 'short_name', 'weight', 'planning')
    ordering = ('name', 'generation', 'aliases', 'short_name', 'weight', 'planning')
    search_fields = ('name', 'generation', 'aliases', 'short_name', 'weight', 'planning')
    list_filter = ('generation', 'short_name', 'weight', 'planning')


@admin.register(Os)
class OsAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'aliases', 'planning', 'weight', 'shortcut')
    ordering = ('name', 'group', 'aliases', 'planning', 'weight', 'shortcut')
    search_fields = ('name', 'group', 'aliases', 'planning', 'weight', 'shortcut')
    list_filter = ('planning', 'weight', 'shortcut')


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('test_status', 'priority')
    ordering = ('test_status', 'priority')
    search_fields = ('test_status', 'priority')
    list_filter = ('test_status', 'priority')
