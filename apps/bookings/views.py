from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Reserva, Programa
from apps.infrastructure.models import Ambiente
from apps.directory.models import Instructor
from datetime import datetime

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

    query = request.GET.get('q', '').strip()
    mis_reservas = Reserva.objects.select_related('ambiente', 'instructor', 'user').order_by('-fecha_inicio')
    
    if query:
        # Intentamos detectar si el usuario ingresó una fecha
        search_date = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
            try:
                search_date = datetime.strptime(query, fmt).date()
                break
            except ValueError:
                continue

        if search_date:
            # Si es fecha, filtramos reservas que cubran ese día específico
            mis_reservas = mis_reservas.filter(fecha_inicio__lte=search_date, fecha_fin__gte=search_date)
        else:
            mis_reservas = mis_reservas.filter(
                Q(ambiente__nombre__icontains=query) | 
                Q(materia__icontains=query) |
                Q(instructor__nombre__icontains=query) |
                Q(jornada__icontains=query)
            )

    context = {
        'reservations': mis_reservas,
        'query': query,
    }
    return render(request, 'booking_list.html', context)

def environment_bookings(request, ambiente_name):
    if not request.session.get('user_id'):
        return redirect('login')

    query = request.GET.get('q', '').strip()
    reservas_ambiente = Reserva.objects.filter(ambiente__nombre=ambiente_name).select_related('instructor', 'ambiente', 'user')
    
    if query:
        # Intentamos detectar si el usuario ingresó una fecha
        search_date = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
            try:
                search_date = datetime.strptime(query, fmt).date()
                break
            except ValueError:
                continue

        if search_date:
            # Filtramos reservas que estén vigentes en la fecha consultada
            reservas_ambiente = reservas_ambiente.filter(fecha_inicio__lte=search_date, fecha_fin__gte=search_date)
        else:
            reservas_ambiente = reservas_ambiente.filter(
                Q(instructor__nombre__icontains=query) | 
                Q(materia__icontains=query) |
                Q(jornada__icontains=query)
            )

    context = {
        'ambiente': ambiente_name,
        'reservations': reservas_ambiente,
        'query': query,
    }
    return render(request, 'environment_bookings.html', context)

# Vista para el formulario de reserva
def reserve_view(request, ambiente_name):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    if not user_id:
        return redirect('login')

    # Definimos el contexto común para evitar errores de variables faltantes
    context = {
        'ambiente': ambiente_name,
        'instructores': Instructor.objects.all().order_by('nombre'),
        'programas': Programa.objects.all().order_by('nombre'),
        'current_username': username,
        'booking': {},
    }

    if request.method == "POST":
        instructor = request.POST.get('instructor', '').strip().upper()
        materia = request.POST.get('materia', '').strip().upper()
        inicio_raw = request.POST.get('hora_inicio', '')
        fin_raw = request.POST.get('hora_fin', '')
        f_inicio_raw = request.POST.get('fecha_inicio', '')
        f_fin_raw = request.POST.get('fecha_fin', '')

        # Validación de integridad
        if not instructor or not materia or not inicio_raw or not fin_raw or not f_inicio_raw or not f_fin_raw:
            messages.error(request, "Todos los campos de fecha y hora son obligatorios.")
            context['booking'] = request.POST
            return render(request, 'reserve_form.html', context)

        # Convertimos a objetos de fecha y hora para evitar errores 500
        try:
            inicio = datetime.strptime(inicio_raw, '%H:%M').time()
            fin = datetime.strptime(fin_raw, '%H:%M').time()
            d_inicio = datetime.strptime(f_inicio_raw, '%Y-%m-%d').date()
            d_fin = datetime.strptime(f_fin_raw, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Formato de fecha u hora inválido.")
            context['booking'] = request.POST
            return render(request, 'reserve_form.html', context)

        if inicio >= fin:
            messages.error(request, "La hora de inicio debe ser anterior a la de fin.")
            context['booking'] = request.POST
            return render(request, 'reserve_form.html', context)

        if d_inicio > d_fin:
            messages.error(request, "La fecha de inicio no puede ser posterior a la de fin.")
            context['booking'] = request.POST
            return render(request, 'reserve_form.html', context)

        instructor_obj, _ = Instructor.objects.get_or_create(nombre=instructor)
        Programa.objects.get_or_create(nombre=materia)
        ambiente_obj = get_object_or_404(Ambiente, nombre=ambiente_name)

        conflicto = Reserva.objects.filter(
            ambiente=ambiente_obj,
            fecha_inicio__lte=d_fin,
            fecha_fin__gte=d_inicio,
            hora_inicio__lt=fin,
            hora_fin__gt=inicio
        ).select_related('instructor').first()

        if conflicto:
            messages.error(request, f"Ocupado: Reservado por {conflicto.instructor.nombre} del {conflicto.fecha_inicio.strftime('%d/%m/%Y')} al {conflicto.fecha_fin.strftime('%d/%m/%Y')}.")
            context['booking'] = request.POST
            return render(request, 'reserve_form.html', context)

        Reserva.objects.create(
            ambiente=ambiente_obj,
            instructor=instructor_obj,
            materia=materia,
            hora_inicio=inicio, # Django ORM acepta objetos time para TimeField
            hora_fin=fin,
            fecha_inicio=d_inicio,
            fecha_fin=d_fin,
            user_id=user_id,
            jornada=obtener_jornada(inicio_raw)
        )
        
        messages.success(request, f"Reserva exitosa para {ambiente_name} por {instructor}.")
        return redirect('booking_list')
        
    return render(request, 'reserve_form.html', context)

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
    username = request.session.get('username')
    if not user_id:
        return redirect('login')

    reserva = get_object_or_404(Reserva, id=booking_id)

    if user_id != reserva.user_id:
        messages.error(request, "No tienes permiso para editar esta reserva.")
        return redirect('booking_list')

    if request.method == "POST":
        instructor_nombre = request.POST.get('instructor', '').strip().upper()
        materia_nombre = request.POST.get('materia', '').strip().upper()
        inicio_raw = request.POST.get('hora_inicio', '')
        fin_raw = request.POST.get('hora_fin', '')
        fecha_inicio = request.POST.get('fecha_inicio', '')
        fecha_fin = request.POST.get('fecha_fin', '')

        # Asegurar que los datos de tiempo existan antes de comparar
        if not inicio_raw or not fin_raw or not fecha_inicio or not fecha_fin:
            messages.error(request, "Todos los campos de fecha y hora son obligatorios.")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': request.POST, 'instructores': Instructor.objects.all().order_by('nombre'), 'programas': Programa.objects.all().order_by('nombre'), 'current_username': username})

        try:
            inicio = datetime.strptime(inicio_raw, '%H:%M').time()
            fin = datetime.strptime(fin_raw, '%H:%M').time()
            d_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            d_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Formato de hora inválido.")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': request.POST, 'instructores': Instructor.objects.all().order_by('nombre'), 'programas': Programa.objects.all().order_by('nombre'), 'current_username': username})

        if inicio >= fin:
            messages.error(request, "Error: El horario de inicio debe ser anterior al de fin (Formato 24h).")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': request.POST, 'instructores': Instructor.objects.all().order_by('nombre'), 'programas': Programa.objects.all().order_by('nombre'), 'current_username': username})

        if d_inicio > d_fin:
            messages.error(request, "Error: La fecha de inicio no puede ser posterior a la fecha de fin.")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': request.POST, 'instructores': Instructor.objects.all().order_by('nombre'), 'programas': Programa.objects.all().order_by('nombre'), 'current_username': username})

        # Validación de solapamiento (excluyendo la reserva que estamos editando)
        conflicto = Reserva.objects.filter(
            ambiente=reserva.ambiente,
            fecha_inicio__lte=d_fin,
            fecha_fin__gte=d_inicio,
            hora_inicio__lt=fin,
            hora_fin__gt=inicio
        ).exclude(id=reserva.id).select_related('instructor').first()

        if conflicto:
            messages.error(request, f"Conflicto con la reserva de {conflicto.instructor.nombre}.")
            return render(request, 'reserve_form.html', {'ambiente': reserva.ambiente.nombre, 'booking': request.POST, 'instructores': Instructor.objects.all().order_by('nombre'), 'programas': Programa.objects.all().order_by('nombre'), 'current_username': username})
        
        # Actualizar instructor y programa de forma independiente
        instructor_obj, _ = Instructor.objects.get_or_create(nombre=instructor_nombre)
        Programa.objects.get_or_create(nombre=materia_nombre)
        
        reserva.instructor = instructor_obj
        reserva.materia = materia_nombre
        reserva.hora_inicio = inicio
        reserva.hora_fin = fin
        reserva.fecha_inicio = d_inicio
        reserva.fecha_fin = d_fin
        reserva.jornada = obtener_jornada(inicio_raw)
        reserva.save()

        messages.success(request, "Reserva actualizada exitosamente.")
        return redirect('booking_list')
    
    return render(request, 'reserve_form.html', {
        'ambiente': reserva.ambiente.nombre, 
        'booking': reserva, 
        'instructores': Instructor.objects.all().order_by('nombre'),
        'programas': Programa.objects.all().order_by('nombre'),
        'current_username': username
    })
