import os
import django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banco.settings')
django.setup()

from django.contrib.auth.models import User, Group
from banking.models import Cliente, CuentaBancaria

def run():
    if User.objects.exists():
        print("La base de datos ya tiene usuarios.")
        return

    # Admin
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superusuario 'admin' creado (password: admin)")

    # Cliente 1
    cliente1_user = User.objects.create_user('cliente1', 'cliente1@example.com', 'cliente1')
    grupo_cli, _ = Group.objects.get_or_create(name='cliente')
    cliente1_user.groups.add(grupo_cli)
    
    cli1 = Cliente.objects.create(
        user=cliente1_user,
        nombre_completo='Juan Perez',
        numero_identificacion='123456789',
        email='cliente1@example.com',
        telefono='5551234',
        direccion='Calle Falsa 123',
        fecha_nacimiento=date(1990, 5, 15)
    )
    
    CuentaBancaria.objects.create(
        cliente=cli1,
        tipo=CuentaBancaria.TipoCuenta.AHORROS,
        saldo=Decimal('1500.00'),
        fecha_apertura=date.today(),
        estado=CuentaBancaria.Estado.ACTIVA
    )
    
    # Cliente 2
    cliente2_user = User.objects.create_user('cliente2', 'cliente2@example.com', 'cliente2')
    cliente2_user.groups.add(grupo_cli)
    
    cli2 = Cliente.objects.create(
        user=cliente2_user,
        nombre_completo='Maria Garcia',
        numero_identificacion='987654321',
        email='cliente2@example.com',
        telefono='5559876',
        direccion='Avenida Siempre Viva 742',
        fecha_nacimiento=date(1992, 10, 20)
    )
    
    CuentaBancaria.objects.create(
        cliente=cli2,
        tipo=CuentaBancaria.TipoCuenta.CORRIENTE,
        saldo=Decimal('3000.00'),
        fecha_apertura=date.today(),
        estado=CuentaBancaria.Estado.ACTIVA
    )

    print("Clientes de prueba creados ('cliente1', 'cliente2') (password igual a su username).")

if __name__ == '__main__':
    run()
