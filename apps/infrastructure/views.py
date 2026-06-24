from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.bookings.models import Reserva # Importamos el modelo de la DB
from .models import Sede, Ambiente
from django.utils.text import slugify

# Vista para listar las sedes y ambientes
def environment_list(request):
    if not request.session.get('user_id'):
        return redirect('login')
    sedes = Sede.objects.all()
    return render(request, 'environment_list.html', {'sedes': sedes})

# Vista para mostrar los ambientes específicos de una sede
def environment_detail(request, sede_slug):
    if not request.session.get('user_id'):
        return redirect('login')
    sede = get_object_or_404(Sede, slug=sede_slug)
    ambientes = sede.ambientes.all()

    context = {
        'sede': sede,
        'ambientes': ambientes,
        'sede_slug': sede_slug, # Lo pasamos para construir las URLs en el template
        'reservations': Reserva.objects.all(), # Ahora las traemos de la base de datos
    }
    return render(request, 'environment_detail.html', context)

# Vista para agregar un nuevo ambiente a una sede
def add_environment(request, sede_slug):
    if not request.session.get('user_id'):
        return redirect('login')
    
    if request.method == "POST":
        sede = get_object_or_404(Sede, slug=sede_slug)
        nombre = request.POST.get('nombre_ambiente').upper()
        inventario = request.POST.get('inventario', '')
        if nombre:
            Ambiente.objects.get_or_create(
                nombre=nombre, 
                sede=sede, 
                defaults={'inventario': inventario}
            )
            messages.success(request, f"Ambiente '{nombre}' agregado exitosamente.")
    return redirect('environment_detail', sede_slug=sede_slug)

# Vista para eliminar un ambiente de una sede
def delete_environment(request, sede_slug, ambiente_name):
    if not request.session.get('user_id'):
        return redirect('login')

    sede = get_object_or_404(Sede, slug=sede_slug)
    ambiente = get_object_or_404(Ambiente, nombre=ambiente_name, sede=sede)
    ambiente.delete()
    messages.success(request, f"Ambiente '{ambiente_name}' eliminado correctamente.")
    return redirect('environment_detail', sede_slug=sede_slug)

# Vista para modificar el nombre de un ambiente existente
def edit_environment(request, sede_slug, ambiente_name):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.method == "POST":
        sede = get_object_or_404(Sede, slug=sede_slug)
        ambiente = get_object_or_404(Ambiente, nombre=ambiente_name, sede=sede)
        nuevo_nombre = request.POST.get('nuevo_nombre').upper()
        inventario = request.POST.get('inventario', '')
        if nuevo_nombre:
            ambiente.nombre = nuevo_nombre
            ambiente.inventario = inventario
            ambiente.save()
            messages.success(request, f"Ambiente '{ambiente_name}' actualizado a '{nuevo_nombre}'.")
    return redirect('environment_detail', sede_slug=sede_slug)

# Vista para agregar una nueva sede institucional
def add_sede(request):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.method == "POST":
        nombre = request.POST.get('nombre_sede')
        descripcion = request.POST.get('descripcion', '')
        # Usamos slugify para manejar tildes y caracteres especiales correctamente
        slug = slugify(nombre)

        Sede.objects.get_or_create(
            slug=slug,
            defaults={
                'nombre': nombre,
                'descripcion': descripcion,
                'icon': 'bi-building'
            }
        )
        messages.success(request, f"Sede '{nombre}' gestionada exitosamente.")
    return redirect('environment_list')

# Vista para modificar la información de una sede
def edit_sede(request, sede_slug):
    if not request.session.get('user_id'):
        return redirect('login')

    sede = get_object_or_404(Sede, slug=sede_slug)
    if request.method == "POST":
        sede.nombre = request.POST.get('nuevo_nombre')
        sede.descripcion = request.POST.get('nueva_descripcion')
        sede.save()
        messages.success(request, "Información de la sede actualizada.")
    return redirect('environment_list')

# Vista para eliminar una sede
def delete_sede(request, sede_slug):
    if not request.session.get('user_id'):
        return redirect('login')

    sede = get_object_or_404(Sede, slug=sede_slug)
    
    # Si el método es POST, significa que el usuario confirmó la eliminación
    if request.method == 'POST':
        nombre_sede = sede.nombre
        sede.delete()
        messages.success(request, f'La sede "{nombre_sede}" y todos sus ambientes han sido eliminados.')
        return redirect('environment_list')

    # Si el método es GET, muestra la página de confirmación
    return render(request, 'confirmar_eliminacion_sede.html', {'sede': sede})
