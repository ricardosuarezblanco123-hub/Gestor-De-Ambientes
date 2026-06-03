from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Reserva
from apps.infrastructure.models import Ambiente
from apps.directory.models import Instructor

# Función auxiliar para determinar la jornada según la hora de inicio
def obtener_jornada(hora_str):
    if not hora_str or ':' not in hora_str:
        return "DÍA"
    hora = int(hora_str.split(':')[0])
    if 6 <= hora < 12:
        return "DÍA"
    elif 12 <= hora < 18:
        return "TARDE"
    else:
        return "NOCHE"

def booking_list(request):
    # Verificación manual
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    # Filtramos usando el ORM de Django
    mis_reservas = Reserva.objects.filter(user_id=user_id).select_related('ambiente', 'instructor').order_by('-fecha_inicio')
    context = {
        'reservations': mis_reservas,
    }
    return render(request, 'booking_list.html', context)

def environment_bookings(request, ambiente_name):
    if not request.session.get('user_id'):
        return redirect('login')

    # Filtramos por el nombre del ambiente relacionado
    reservas_ambiente = Reserva.objects.filter(ambiente__nombre=ambiente_name).select_related('instructor', 'ambiente')
    context = {
        'ambiente': ambiente_name,
        'reservations': reservas_ambiente,
    }
    return render(request, 'environment_bookings.html', context)

# Vista para el formulario de reserva
def reserve_view(request, ambiente_name):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == "POST":
        instructor = request.POST.get('instructor', '').strip().upper()
        materia = request.POST.get('materia', '').strip().upper()
        inicio = request.POST.get('hora_inicio', '')
        fin = request.POST.get('hora_fin', '')
        fecha_inicio = request.POST.get('fecha_inicio', '')
        fecha_fin = request.POST.get('fecha_fin', '')

        # Validación de integridad: La reserva debe tener una duración positiva
        if not inicio or not fin:
            messages.error(request, "Los campos de hora son obligatorios.")
            return render(request, 'reserve_form.html', {'ambiente': ambiente_name, 'booking': request.POST, 'instructores': Instructor.objects.all()})

        if inicio <= fin:
            messages.error(request, "Error: La hora de inicio debe ser menor a la hora de fin.")
            return render(request, 'reserve_form.html', {'ambiente': ambiente_name, 'booking': request.POST, 'instructores': Instructor.objects.all()})

        # Obtener o crear instructor en el directorio y capturar el objeto
        instructor_obj, _ = Instructor.objects.get_or_create(nombre=instructor, defaults={'materia': materia})
        
        # Obtener objeto ambiente
        ambiente_obj = get_object_or_404(Ambiente, nombre=ambiente_name)

        # Validación de disponibilidad en la DB
        solapada = Reserva.objects.filter(
            ambiente=ambiente_obj,
            fecha_inicio__lte=fecha_fin,
            fecha_fin__gte=fecha_inicio,
            hora_inicio__lt=fin,
            hora_fin__gt=inicio
        ).exists()

        if solapada:
            print(f"DEBUG: Reserva solapada detectada para el ambiente {ambiente_name}")
            messages.error(request, "El ambiente ya está ocupado en ese horario.")
            return render(request, 'reserve_form.html', {'ambiente': ambiente_name, 'booking': request.POST, 'instructores': Instructor.objects.all()})

        # Guardar en la base de datos
        Reserva.objects.create(
            ambiente=ambiente_obj,
            instructor=instructor_obj,
            materia=materia,
            hora_inicio=inicio,
            hora_fin=fin,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            user_id=user_id,
            jornada=obtener_jornada(inicio)
        )
        
        print(f"DEBUG: Reserva guardada exitosamente para {instructor}")
        messages.success(request, f"Reserva exitosa para {ambiente_name} por {instructor}.")
        return redirect('booking_list')
        
    return render(request, 'reserve_form.html', {'ambiente': ambiente_name, 'instructores': Instructor.objects.all()})

def delete_booking(request, booking_id):
    # Verificación manual de sesión
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    reserva = get_object_or_404(Reserva, id=booking_id)
    # Es más eficiente comparar directamente con user_id para evitar una consulta extra a la DB
    if user_id == reserva.user_id:
        reserva.delete()
        messages.success(request, "Reserva eliminada exitosamente.")
    else:
        messages.error(request, "No tienes permiso para eliminar esta reserva.")
    return redirect('booking_list')

def edit_booking(request, booking_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    reserva = get_object_or_404(Reserva, id=booking_id)

    if user_id != reserva.user_id:
        messages.error(request, "No tienes permiso para editar esta reserva.")
        return redirect('booking_list')

    if request.method == "POST":
        instructor_nombre = request.POST.get('instructor', '').strip().upper()
        materia_nombre = request.POST.get('materia', '').strip().upper()
        inicio = request.POST.get('hora_inicio', '')
        fin = request.POST.get('hora_fin', '')
        fecha_inicio = request.POST.get('fecha_inicio', '')
        fecha_fin = request.POST.get('fecha_fin', '')

        # Asegurar que los datos de tiempo existan antes de comparar
        if not inicio or not fin:
            messages.error(request, "Debe especificar horas válidas para la reserva.")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': reserva, 'instructores': Instructor.objects.all()})

        if inicio >= fin:
            messages.error(request, "Error: El horario ingresado no es válido (inicio >= fin).")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': reserva, 'instructores': Instructor.objects.all()})

        # Validación de solapamiento (excluyendo la reserva que estamos editando)
        solapada = Reserva.objects.filter(
            ambiente=reserva.ambiente,
            fecha_inicio__lte=fecha_fin,
            fecha_fin__gte=fecha_inicio,
            hora_inicio__lt=fin,
            hora_fin__gt=inicio
        ).exclude(id=reserva.id).exists()

        if solapada:
            messages.error(request, "El ambiente ya está ocupado en ese horario.")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': reserva, 'instructores': Instructor.objects.all()})
        
        # Sincronizar con la tabla de instructores para que siempre quede el registro
        instructor_obj, _ = Instructor.objects.get_or_create(nombre=instructor_nombre, defaults={'materia': materia_nombre})
        
        reserva.instructor = instructor_obj
        reserva.materia = materia_nombre
        reserva.hora_inicio = inicio
        reserva.hora_fin = fin
        reserva.fecha_inicio = fecha_inicio
        reserva.fecha_fin = fecha_fin
        reserva.jornada = obtener_jornada(inicio)
        reserva.save()

        messages.success(request, "Reserva actualizada exitosamente.")
        return redirect('booking_list')
    
    return render(request, 'reserve_form.html', {
        'ambiente': reserva.ambiente.nombre, 
        'booking': reserva, 
        'instructores': Instructor.objects.all()
    })
