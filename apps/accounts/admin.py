from django.contrib import admin
from django.contrib.auth.hashers import make_password
from apps.accounts.models import role, user

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'is_active')
    
    def save_model(self, request, obj, form, change):
        # Si la contraseña no está encriptada (no empieza con pbkdf2), la encriptamos
        if not obj.password.startswith('pbkdf2_sha256$'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

admin.site.register(user, UserAdmin)
admin.site.register(role)
