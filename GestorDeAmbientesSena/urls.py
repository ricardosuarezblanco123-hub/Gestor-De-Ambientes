"""
URL configuration for GestorDeAmbientesSena project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from apps.accounts.views import login_view, logout_view, profile_view, custom_register_view, delete_user, recover_password_view, reset_password_view # Importa las vistas de cuentas
from apps.bookings.views import booking_list, reserve_view, delete_booking, edit_booking, environment_bookings # Importa las vistas de reservas
from apps.directory.views import directory_list
from apps.infrastructure.views import environment_list, environment_detail, add_environment, delete_environment, edit_environment, add_sede, edit_sede, delete_sede
# Definición de las rutas (URLs) de todo el sitio web
urlpatterns = [
    # Ruta principal (vacía): Ahora redirigimos a la lista de sedes para mejor flujo
    path('', environment_list, name='index'),

    # Panel de administración de Django
    path('admin/', admin.site.urls),
    
    # Rutas para el manejo de usuarios (Login, Logout y Dashboard)
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', custom_register_view, name='register'),
    path('custom-register/', custom_register_view, name='custom_register'),
    path('profile/', profile_view, name='profile'),
    path('recover-password/', recover_password_view, name='recover_password'),
    path('reset-password/<str:token>/', reset_password_view, name='reset_password'),
    path('accounts/delete/<int:user_id>/', delete_user, name='delete_user'),
    
    # Rutas para las funcionalidades del negocio (Reservas, Directorio, Ambientes)
    path('bookings/', booking_list, name='booking_list'),
    path('bookings/ambiente/<str:ambiente_name>/', environment_bookings, name='environment_bookings'), # Nueva ruta individual
    path('bookings/delete/<int:booking_id>/', delete_booking, name='delete_booking'), # Ruta para eliminar
    path('bookings/edit/<int:booking_id>/', edit_booking, name='edit_booking'),     # Ruta para editar
    path('reserve/<str:ambiente_name>/', reserve_view, name='reserve_view'),
    path('directory/', directory_list, name='directory_list'),
    path('environments/', environment_list, name='environment_list'),
    path('environments/<str:sede_slug>/', environment_detail, name='environment_detail'),
    path('environments/<str:sede_slug>/add/', add_environment, name='add_environment'), # Ruta para agregar
    path('environments/<str:sede_slug>/delete/<str:ambiente_name>/', delete_environment, name='delete_environment'), # Ruta para eliminar
    path('environments/<str:sede_slug>/edit/<str:ambiente_name>/', edit_environment, name='edit_environment'), # Ruta para editar
    path('sedes/add/', add_sede, name='add_sede'), # Nueva ruta para agregar sede
    path('sedes/edit/<str:sede_slug>/', edit_sede, name='edit_sede'), # Nueva ruta para editar sede
    path('sedes/delete/<str:sede_slug>/', delete_sede, name='delete_sede'), # Nueva ruta para eliminar sede
]
