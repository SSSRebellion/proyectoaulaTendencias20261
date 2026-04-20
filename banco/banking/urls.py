from django.urls import include, path
from rest_framework.routers import DefaultRouter

<<<<<<< HEAD
from .views import ClienteViewSet, CuentaBancariaViewSet, TransferenciaViewSet
=======
from .views import ClienteViewSet, CuentaBancariaViewSet
>>>>>>> 03e623ade403996219ded2a3524448cf8d03d531

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'cuentas', CuentaBancariaViewSet, basename='cuenta')
<<<<<<< HEAD
router.register(r'transferencias', TransferenciaViewSet, basename='transferencia')
=======
>>>>>>> 03e623ade403996219ded2a3524448cf8d03d531

urlpatterns = [
    path('', include(router.urls)),
]
