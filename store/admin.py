from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from store.models import App, AppVersion, Category, ContactMessage, Download, Screenshot, User, WebsiteSettings

admin.site.register(Category)
admin.site.register(App)
admin.site.register(Screenshot)
admin.site.register(Download)
admin.site.register(AppVersion)
admin.site.register(ContactMessage)
admin.site.register(WebsiteSettings)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
