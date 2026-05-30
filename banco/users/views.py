from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from banking.models import Cliente

from .serializers import (
    BancoTokenObtainPairSerializer,
    CrearUsuarioConRolSerializer,
    RegistroClienteSerializer,
)


class RegistroClienteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'mensaje': 'Cliente registrado. Use /api/auth/token/ para obtener tokens JWT.',
            },
            status=status.HTTP_201_CREATED,
        )


class TokenObtainPairViewSinMensajeExtra(TokenObtainPairView):
    serializer_class = BancoTokenObtainPairSerializer


class UsuarioActualView(APIView):
    """Perfil y rol del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'es_administrador': user.is_staff or user.is_superuser,
        }
        try:
            cliente = user.cliente
        except Cliente.DoesNotExist:
            cliente = None
        if cliente:
            data['cliente_id'] = cliente.id
            data['nombre_completo'] = cliente.nombre_completo
        return Response(data)


class CrearUsuarioConRolView(APIView):
    """
    Crea un usuario con rol administrador_bancario o cliente.
    Requiere JWT de un usuario staff (administrador bancario).
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = CrearUsuarioConRolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'grupos': list(user.groups.values_list('name', flat=True)),
                'mensaje': 'Usuario creado.',
            },
            status=status.HTTP_201_CREATED,
        )
