from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CrearUsuarioConRolView,
    RegistroClienteView,
    TokenObtainPairViewSinMensajeExtra,
)

urlpatterns = [
    path('usuarios/', CrearUsuarioConRolView.as_view(), name='auth-crear-usuario-rol'),
    path('registro/', RegistroClienteView.as_view(), name='auth-registro'),
    path('token/', TokenObtainPairViewSinMensajeExtra.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
