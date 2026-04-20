from django.http import JsonResponse


def inicio(request):
    base = request.build_absolute_uri('/').rstrip('/')
    return JsonResponse(
        {
            'mensaje': 'API Banco — servidor en ejecución',
            'enlaces': {
                'admin': f'{base}/admin/',
                'registro': f'{base}/api/auth/registro/',
                'crear_usuario_rol': f'{base}/api/auth/usuarios/',
                'token_jwt': f'{base}/api/auth/token/',
                'clientes': f'{base}/api/clientes/',
                'cuentas': f'{base}/api/cuentas/',
                'transferencias': f'{base}/api/transferencias/',
            },
        }
    )
