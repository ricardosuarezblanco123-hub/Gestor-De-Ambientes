from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import user as custom_user, role as account_role
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.core.signing import Signer, BadSignature

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

        # Validación de longitud mínima en el inicio de sesión
        if len(password_val) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
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

    user_record = get_object_or_404(custom_user, id=user_id)
    all_users = custom_user.objects.all()

    if request.method == "POST":
        # Usamos un campo 'action' para saber qué formulario se envió
        action = request.POST.get('action')

        if action == "update_info":
            new_username = request.POST.get('username', '').strip()
            new_email = request.POST.get('email', '').strip()

            # Validar que no existan duplicados en otros registros
            if custom_user.objects.filter(username__iexact=new_username).exclude(id=user_id).exists():
                messages.error(request, "El nombre de usuario ya está siendo utilizado por otra cuenta.")
            elif new_email and custom_user.objects.filter(email__iexact=new_email).exclude(id=user_id).exists():
                messages.error(request, "Este correo electrónico ya está registrado con otro usuario.")
            else:
                user_record.username = new_username
                user_record.email = new_email
                user_record.save()
                messages.success(request, "Tu perfil ha sido actualizado correctamente.")
            
        elif action == "change_password":
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            # Validaciones de seguridad
            if not check_password(old_password, user_record.password):
                messages.error(request, "La contraseña actual es incorrecta.")
            elif new_password != confirm_password:
                messages.error(request, "Las nuevas contraseñas no coinciden.")
            elif len(new_password) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            elif not any(c.isupper() for c in new_password):
                messages.error(request, "La contraseña debe incluir al menos una letra mayúscula.")
            elif not any(c.islower() for c in new_password):
                messages.error(request, "La contraseña debe incluir al menos una letra minúscula.")
            elif not any(c.isdigit() for c in new_password):
                messages.error(request, "La contraseña debe incluir al menos un número.")
            else:
                user_record.password = make_password(new_password)
                user_record.save()
                messages.success(request, "Contraseña actualizada exitosamente.")

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
        username_val = request.POST.get('username', '').strip()
        password_val = request.POST.get('password', '').strip()
        email_val = request.POST.get('email', '').strip()

        if username_val and password_val:
            # Verificamos duplicados antes de proceder
            if custom_user.objects.filter(username__iexact=username_val).exists():
                messages.error(request, "El nombre de usuario ya se encuentra registrado.")
                return render(request, "custom_register.html")
            
            if email_val and custom_user.objects.filter(email__iexact=email_val).exists():
                messages.error(request, "Este correo electrónico ya está en uso.")
                return render(request, "custom_register.html")

            # Validación estricta de seguridad para nuevos registros
            if len(password_val) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
                return render(request, "custom_register.html")
            elif not any(c.isupper() for c in password_val):
                messages.error(request, "La contraseña debe incluir al menos una letra mayúscula.")
                return render(request, "custom_register.html")
            elif not any(c.islower() for c in password_val):
                messages.error(request, "La contraseña debe incluir al menos una letra minúscula.")
                return render(request, "custom_register.html")
            elif not any(c.isdigit() for c in password_val):
                messages.error(request, "La contraseña debe incluir al menos un número.")
                return render(request, "custom_register.html")

            # Guardamos manualmente en la tabla personalizada 'accounts_user'
            # Usamos make_password para que la clave sea segura (formato de 128 caracteres)
            new_user = custom_user.objects.create(
                username=username_val,
                password=make_password(password_val),
                email=email_val,
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

    return render(request, "custom_register.html")

def recover_password_view(request):
    if request.method == "POST":
        email_input = request.POST.get('email', '').strip()
        # Buscamos al usuario en la base de datos por el correo ingresado
        user_record = custom_user.objects.filter(email__iexact=email_input).first()
        
        if user_record and user_record.email:
            signer = Signer()
            # Firmamos el ID para generar un token seguro y sin caracteres especiales
            token = signer.sign(str(user_record.id))
            
            url_reset = reverse('reset_password', kwargs={'token': token})
            full_url = request.build_absolute_uri(url_reset)

            # Texto del correo sin tildes ni eñes para evitar fallos de codificacion ASCII en el servidor SMTP
            asunto = 'Recuperacion de Acceso - Gestor de Ambientes'
            safe_username = user_record.username.encode('ascii', 'ignore').decode('ascii')
            mensaje = f'Hola {safe_username},\n\nHa solicitado restablecer su clave. Use el siguiente enlace: {full_url}'
            
            try:
                # Usamos estrictamente el correo que esta en el registro de la DB
                send_mail(asunto, mensaje, None, [user_record.email])
                messages.success(request, f"Se ha enviado un enlace de recuperacion al correo: {user_record.email}")
            except Exception:
                messages.error(request, "Error de autenticacion (535). Revisa que la clave de 16 letras en settings.py sea correcta.")

            return redirect('login')
        messages.error(request, "No se encontro ningun usuario con ese correo o el usuario no tiene correo registrado.")
    return render(request, "recover_password.html")

def reset_password_view(request, token):
    signer = Signer()
    try:
        user_id = signer.unsign(token)
    except BadSignature:
        messages.error(request, "El enlace de recuperación es inválido o ha expirado.")
        return redirect('login')

    if request.method == "POST":
        new_password = request.POST.get('password', '').strip()
        
        if not new_password:
            messages.error(request, "La nueva contraseña no puede estar vacía.")
            return render(request, "reset_password.html", {'token': token})
        
        # Validación estricta de seguridad
        if len(new_password) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
        elif not any(c.isupper() for c in new_password):
            messages.error(request, "Debe incluir al menos una letra mayúscula.")
        elif not any(c.islower() for c in new_password):
            messages.error(request, "Debe incluir al menos una letra minúscula.")
        elif not any(c.isdigit() for c in new_password):
            messages.error(request, "Debe incluir al menos un número.")
        else:
            user_record = get_object_or_404(custom_user, id=user_id)
            user_record.password = make_password(new_password)
            user_record.save(update_fields=['password'])
            messages.success(request, "Contraseña actualizada exitosamente.")
            return redirect('login')

    return render(request, "reset_password.html", {'token': token})
