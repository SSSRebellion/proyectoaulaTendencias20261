from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, CuentaBancariaViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'cuentas', CuentaBancariaViewSet, basename='cuenta')

urlpatterns = [
    path('', include(router.urls)),
]
