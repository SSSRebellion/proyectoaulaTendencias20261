from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from banking.models import Cliente, CuentaBancaria, Movimiento, Transferencia


class OperacionesBancariasAPITest(TestCase):
    """Pruebas de API críticas: saldo, transferencias y permisos por rol."""

    def setUp(self):
        self.api = APIClient()

        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='TestPass12345',
            is_staff=True,
        )

        self.user_a = User.objects.create_user(
            username='cliente_a',
            email='a@test.com',
            password='TestPass12345',
            is_staff=False,
        )
        grupo_cli, _ = Group.objects.get_or_create(name='cliente')
        self.user_a.groups.add(grupo_cli)
        self.cli_a = Cliente.objects.create(
            user=self.user_a,
            nombre_completo='Cliente A',
            numero_identificacion='ID-A-001',
            email='a@test.com',
            telefono='300',
            direccion='Calle A',
            fecha_nacimiento=date(1990, 1, 1),
        )
        self.cuenta_a = CuentaBancaria.objects.create(
            cliente=self.cli_a,
            tipo=CuentaBancaria.TipoCuenta.AHORROS,
            saldo=Decimal('1000.00'),
            fecha_apertura=date(2025, 1, 1),
            estado=CuentaBancaria.Estado.ACTIVA,
        )

        self.user_b = User.objects.create_user(
            username='cliente_b',
            email='b@test.com',
            password='TestPass12345',
            is_staff=False,
        )
        self.user_b.groups.add(grupo_cli)
        self.cli_b = Cliente.objects.create(
            user=self.user_b,
            nombre_completo='Cliente B',
            numero_identificacion='ID-B-001',
            email='b@test.com',
            telefono='301',
            direccion='Calle B',
            fecha_nacimiento=date(1991, 2, 2),
        )
        self.cuenta_b = CuentaBancaria.objects.create(
            cliente=self.cli_b,
            tipo=CuentaBancaria.TipoCuenta.CORRIENTE,
            saldo=Decimal('500.00'),
            fecha_apertura=date(2025, 1, 2),
            estado=CuentaBancaria.Estado.ACTIVA,
        )

    def _auth(self, user):
        self.api.force_authenticate(user=user)

    def test_deposito_actualiza_saldo_y_registra_movimiento(self):
        self._auth(self.admin)
        r = self.api.post(
            f'/api/cuentas/{self.cuenta_a.id}/deposito/',
            {'monto': '250.50'},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.cuenta_a.refresh_from_db()
        self.assertEqual(self.cuenta_a.saldo, Decimal('1250.50'))
        self.assertEqual(Movimiento.objects.filter(cuenta=self.cuenta_a).count(), 1)
        mov = Movimiento.objects.get(cuenta=self.cuenta_a)
        self.assertEqual(mov.tipo, Movimiento.Tipo.DEPOSITO)
        self.assertEqual(mov.saldo_resultante, Decimal('1250.50'))

    def test_retiro_saldo_insuficiente(self):
        self._auth(self.admin)

        self.cuenta_a.saldo = Decimal('10.00')
        self.cuenta_a.save()

        r = self.api.post(
            f'/api/cuentas/{self.cuenta_a.id}/retiro/',
            {'monto': '500.00'},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.cuenta_a.refresh_from_db()
        self.assertEqual(self.cuenta_a.saldo, Decimal('10.00'))
        self.assertEqual(Movimiento.objects.filter(cuenta=self.cuenta_a).count(), 0)

    def test_transferencia_atomica_y_dos_movimientos(self):
        self._auth(self.admin)
        saldo_antes_a = self.cuenta_a.saldo
        saldo_antes_b = self.cuenta_b.saldo
        monto_tr = Decimal('200.00')

        r = self.api.post(
            '/api/transferencias/',
            {
                'cuenta_origen': self.cuenta_a.id,
                'cuenta_destino': self.cuenta_b.id,
                'monto': str(monto_tr),
            },
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        self.cuenta_a.refresh_from_db()
        self.cuenta_b.refresh_from_db()
        self.assertEqual(self.cuenta_a.saldo, saldo_antes_a - monto_tr)
        self.assertEqual(self.cuenta_b.saldo, saldo_antes_b + monto_tr)

        data = r.json()
        tid = data['id']
        movs = Movimiento.objects.filter(transferencia_id=tid)
        self.assertEqual(movs.count(), 2)
        tipos = set(movs.values_list('tipo', flat=True))
        self.assertEqual(
            tipos,
            {
                Movimiento.Tipo.TRANSFERENCIA_ORIGEN,
                Movimiento.Tipo.TRANSFERENCIA_DESTINO,
            },
        )

    def test_transferencia_saldo_insuficiente_sin_cambios(self):
        self._auth(self.admin)
        self.cuenta_a.saldo = Decimal('50.00')
        self.cuenta_a.save()
        saldo_b_antes = self.cuenta_b.saldo

        r = self.api.post(
            '/api/transferencias/',
            {
                'cuenta_origen': self.cuenta_a.id,
                'cuenta_destino': self.cuenta_b.id,
                'monto': '1000.00',
            },
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.cuenta_a.refresh_from_db()
        self.cuenta_b.refresh_from_db()
        self.assertEqual(self.cuenta_a.saldo, Decimal('50.00'))
        self.assertEqual(self.cuenta_b.saldo, saldo_b_antes)
        self.assertEqual(Transferencia.objects.count(), 0)

    def test_cliente_no_opera_cuenta_ajena(self):
        self._auth(self.user_b)
        r = self.api.post(
            f'/api/cuentas/{self.cuenta_a.id}/deposito/',
            {'monto': '10.00'},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

