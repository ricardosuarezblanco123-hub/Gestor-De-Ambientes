import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestorDeAmbientesSena.settings')
django.setup()

from apps.infrastructure.models import Sede, Ambiente

def poblar():
    # Datos originales que estaban en las vistas
    sedes_data = {
        'SENA CATA': {
            'slug': 'sena-cata',
            'icon': 'bi-building-fill-check',
            'descripcion': 'Sede principal enfocada en tecnologías avanzadas y coordinación técnica.',
            'ambientes': [
                'AMBIENTE 201', 'AMBIENTE 202', 'AMBIENTE 203', 'AMBIENTE 204', 
                'AMBIENTE 205', 'AMBIENTE 206', 'AMBIENTE 207', 'AMBIENTE 208', 
                'BIBLIOTECA', 'BILINGÜISMO', 'GASTRONOMIA', 'SALON MULTIPLE'
            ]
        },
        'Casa de Apoyo': {
            'slug': 'casa-de-apoyo',
            'icon': 'bi-house-gear-fill',
            'descripcion': 'Espacios dedicados al soporte administrativo y bienestar del aprendiz.',
            'ambientes': ['SALA DE JUNTAS', 'OFICINA BIENESTAR']
        },
        'Granja': {
            'slug': 'granja',
            'icon': 'bi-tree-fill',
            'descripcion': 'Ambientes de formación agroindustrial y proyectos productivos sostenibles.',
            'ambientes': ['INVERNADERO', 'ESTABLO', 'APIARIO', 'ZONA DE CULTIVO']
        },
    }

    print("Iniciando carga de datos...")
    for nombre, info in sedes_data.items():
        sede, created = Sede.objects.get_or_create(
            slug=info['slug'],
            defaults={'nombre': nombre, 'descripcion': info['descripcion'], 'icon': info['icon']}
        )
        if created:
            print(f"Sede creada: {nombre}")
        
        for amb_name in info['ambientes']:
            ambiente, amb_created = Ambiente.objects.get_or_create(
                nombre=amb_name, 
                sede=sede,
                defaults={'inventario': 'Inventario inicial pendiente por registrar.'}
            )
            if amb_created:
                print(f"  - Ambiente creado: {amb_name}")

    print("\n¡Proceso finalizado! Ya puedes ver las sedes en la aplicación.")

if __name__ == '__main__':
    poblar()