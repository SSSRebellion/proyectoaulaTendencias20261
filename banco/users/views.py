from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CrearUsuarioConRolSerializer, RegistroClienteSerializer


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
    """Misma vista que SimpleJWT; expuesta bajo nombre del proyecto."""

    pass


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
