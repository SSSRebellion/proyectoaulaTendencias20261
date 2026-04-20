from django.contrib.auth.models import Group, User
from rest_framework import serializers

from banking.models import Cliente


class RolUsuario:
    ADMIN = 'administrador_bancario'
    CLIENTE = 'cliente'


class RegistroClienteSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    nombre_completo = serializers.CharField(max_length=255)
    numero_identificacion = serializers.CharField(max_length=32)
    telefono = serializers.CharField(max_length=32)
    direccion = serializers.CharField()
    fecha_nacimiento = serializers.DateField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este nombre de usuario ya está en uso.')
        return value

    def validate_numero_identificacion(self, value):
        if Cliente.objects.filter(numero_identificacion=value).exists():
            raise serializers.ValidationError('Este número de identificación ya está registrado.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este correo ya está registrado.')
        if Cliente.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este correo ya está registrado como cliente.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_staff=False,
            is_superuser=False,
        )
        grupo, _ = Group.objects.get_or_create(name='cliente')
        user.groups.add(grupo)
        Cliente.objects.create(
            user=user,
            nombre_completo=validated_data['nombre_completo'],
            numero_identificacion=validated_data['numero_identificacion'],
            email=validated_data['email'],
            telefono=validated_data['telefono'],
            direccion=validated_data['direccion'],
            fecha_nacimiento=validated_data['fecha_nacimiento'],
        )
        return user


class CrearUsuarioConRolSerializer(serializers.Serializer):
    """
    Solo para uso interno por administrador bancario (vista con IsAdminUser).
    """

    rol = serializers.ChoiceField(choices=[RolUsuario.ADMIN, RolUsuario.CLIENTE])
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    nombre_completo = serializers.CharField(required=False, allow_blank=True, max_length=255)
    numero_identificacion = serializers.CharField(required=False, allow_blank=True, max_length=32)
    telefono = serializers.CharField(required=False, allow_blank=True, max_length=32)
    direccion = serializers.CharField(required=False, allow_blank=True)
    fecha_nacimiento = serializers.DateField(required=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este nombre de usuario ya está en uso.')
        return value

    def validate(self, attrs):
        if attrs['rol'] == RolUsuario.CLIENTE:
            faltan = []
            for campo in (
                'nombre_completo',
                'numero_identificacion',
                'telefono',
                'direccion',
                'fecha_nacimiento',
            ):
                v = attrs.get(campo)
                if v is None or (isinstance(v, str) and not v.strip()):
                    faltan.append(campo)
            if faltan:
                raise serializers.ValidationError(
                    {c: 'Requerido para rol cliente.' for c in faltan}
                )
        return attrs

    def validate_numero_identificacion(self, value):
        if not value:
            return value
        if Cliente.objects.filter(numero_identificacion=value).exists():
            raise serializers.ValidationError('Este número de identificación ya está registrado.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este correo ya está registrado.')
        if Cliente.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este correo ya está registrado como cliente.')
        return value

    def create(self, validated_data):
        rol = validated_data.pop('rol')
        email = validated_data['email']
        username = validated_data['username']
        password = validated_data['password']

        if rol == RolUsuario.ADMIN:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=False,
            )
            g_admin, _ = Group.objects.get_or_create(name='administrador_bancario')
            user.groups.add(g_admin)
            return user

        validated_data.pop('username')
        validated_data.pop('password')
        validated_data.pop('email')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=False,
            is_superuser=False,
        )
        g_cli, _ = Group.objects.get_or_create(name='cliente')
        user.groups.add(g_cli)
        Cliente.objects.create(
            user=user,
            nombre_completo=validated_data['nombre_completo'],
            numero_identificacion=validated_data['numero_identificacion'],
            email=email,
            telefono=validated_data['telefono'],
            direccion=validated_data['direccion'],
            fecha_nacimiento=validated_data['fecha_nacimiento'],
        )
        return user
