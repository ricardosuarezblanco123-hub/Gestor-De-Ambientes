from django.contrib import admin

from apps.accounts.models import role, user

admin.site.register(user)
admin.site.register(role)
