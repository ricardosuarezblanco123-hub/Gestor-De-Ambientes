from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import user as custom_user, role as account_role
from django.contrib.auth.hashers import make_password, check_password

# Create your views here.

# Vista para manejar el inicio de sesión de los usuarios
def login_view(request):
    # Si el usuario ya tiene sesión iniciada, lo mandamos a donde quería ir o a sedes
    user_id = request.session.get('user_id')
    if user_id:
        # Obtenemos 'next' de la URL o del formulario (POST)
        next_url = request.GET.get('next') or request.POST.get('next')
        # Evitamos redirigir si next es el propio login o está vacío
        if next_url and next_url.strip() and next_url != request.path:
            return redirect(next_url)
        return redirect('add_sede')

    if request.method == "POST":
        username_val = request.POST.get('username', '').strip()
        password_val = request.POST.get('password', '').strip()

        # Validación básica de campos vacíos
        if not username_val or not password_val:
            messages.warning(request, "Por favor, ingrese tanto el usuario como la contraseña.")
            return render(request, "login.html")

        # 1. Búsqueda en la tabla personalizada 'accounts_user'
        # Usamos __iexact para que no importe si el usuario escribe Admin o admin
        user_record = custom_user.objects.filter(
            username__iexact=username_val, 
            is_active=True
        ).first()

        # 2. Verificación de credenciales
        if user_record:
            # Intentamos verificar con la encriptación estándar de Django
            password_correct = check_password(password_val, user_record.password)
            
            # "Salvavidas": Si falla, revisamos si la clave coincide en texto plano (usuarios viejos del Admin)
            if not password_correct and password_val == user_record.password:
                password_correct = True
                # Aprovechamos para encriptarla ahora mismo; así la próxima vez será más seguro
                user_record.password = make_password(password_val)
                user_record.save()

            if password_correct:
                # 4. Iniciar sesión manual
                request.session['user_id'] = int(user_record.id)
                request.session['username'] = user_record.username
                request.session.modified = True  # Forzamos el guardado de la sesión
                request.session.save() # Guardar explícitamente la sesión
                
                messages.success(request, "¡Bienvenido al sistema!")
                
                # Si venía de otra página, lo devolvemos allá, si no, a sedes
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and next_url.strip() and next_url != request.path:
                    return redirect(next_url)
                return redirect('add_sede')

        # Si llegamos aquí es porque el usuario no existe o la contraseña falló
        messages.error(request, "Usuario o contraseña incorrectos.")
            
    # 5. Si no es POST, mostrar el formulario
    return render(request, "login.html")



# Vista para cerrar la sesión actual
def logout_view(request):
    # Limpiamos la sesión manual
    request.session.flush()
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect('login')

# Vista para ver y editar el perfil del usuario
def profile_view(request):
    # Verificación manual de sesión
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user_record = custom_user.objects.get(id=user_id)
    all_users = custom_user.objects.all()

    if request.method == "POST":
        user_record.username = request.POST.get('username')
        user_record.save()
        messages.success(request, "Tu perfil ha sido actualizado correctamente.")
        return redirect('profile')
    return render(request, 'profile.html', {'user': user_record, 'all_users': all_users})

# Eliminamos register_view estándar porque crea usuarios en la tabla equivocada
def register_view(request):
    return redirect('custom_register')

def delete_user(request, user_id):
    # Verificación manual de sesión
    admin_id = request.session.get('user_id')
    if not admin_id:
        return redirect('login')
    
    user_to_delete = get_object_or_404(custom_user, id=user_id)
    
    if user_to_delete.id == admin_id:
        messages.warning(request, "No puedes eliminar tu propio perfil desde la lista de gestión.")
    else:
        user_to_delete.delete()
        messages.success(request, "Perfil eliminado exitosamente.")
    return redirect('profile')

# Vista para el registro manual en la tabla personalizada 
def custom_register_view(request):
    # Permitimos el registro sin estar logueado para que nuevos usuarios puedan unirse

    if request.method == "POST":
        username_val = request.POST.get('username')
        password_val = request.POST.get('password')
        role_id_val = request.POST.get('role_id')

        if username_val and password_val:
            # Buscamos el objeto Rol si se seleccionó uno
            role_obj = None
            if role_id_val:
                role_obj = account_role.objects.filter(id=role_id_val).first()

            # Guardamos manualmente en la tabla personalizada 'accounts_user'
            # Usamos make_password para que la clave sea segura (formato de 128 caracteres)
            new_user = custom_user.objects.create(
                username=username_val,
                password=make_password(password_val),
                role=role_obj,
                is_active=True
            )
            
            # AUTO-LOGIN: Iniciamos la sesión inmediatamente para que no lo rebote al login
            request.session['user_id'] = new_user.id
            request.session['username'] = new_user.username
            request.session.save() # Guardar explícitamente la sesión

            messages.success(request, f"¡Bienvenido, {username_val}! Tu cuenta ha sido creada.")
            return redirect('add_sede')
        else:
            messages.error(request, "El nombre de usuario y la contraseña son obligatorios.")

    roles_list = account_role.objects.all()
    return render(request, "custom_register.html", {"roles": roles_list})
