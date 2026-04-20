from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, CuentaBancariaViewSet, TransferenciaViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'cuentas', CuentaBancariaViewSet, basename='cuenta')
router.register(r'transferencias', TransferenciaViewSet, basename='transferencia')

urlpatterns = [
    path('', include(router.urls)),
]
