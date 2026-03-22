from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from banking.models import Cliente

from .forms import CrearUsuarioBancoForm

User = get_user_model()

if admin.site.is_registered(User):
    admin.site.unregister(User)


class ClienteInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        user = self.instance
        if not user or not user.pk:
            return
        if not (user.is_staff or user.is_superuser):
            return
        for form in self.forms:
            cd = getattr(form, 'cleaned_data', None) or {}
            if cd.get('DELETE'):
                continue
            if form.instance.pk:
                raise ValidationError(
                    'Un usuario administrador no puede tener ficha de cliente.'
                )
            if any(
                cd.get(name)
                for name in (
                    'nombre_completo',
                    'numero_identificacion',
                    'email',
                    'telefono',
                    'direccion',
                    'fecha_nacimiento',
                )
            ):
                raise ValidationError(
                    'Un usuario administrador no puede tener ficha de cliente.'
                )


class ClienteInline(admin.StackedInline):
    model = Cliente
    fk_name = 'user'
    formset = ClienteInlineFormSet
    can_delete = True
    extra = 0
    max_num = 1
    fields = (
        'nombre_completo',
        'numero_identificacion',
        'email',
        'telefono',
        'direccion',
        'fecha_nacimiento',
    )


@admin.register(User)
class UsuarioBancoAdmin(UserAdminBase):
    add_form = CrearUsuarioBancoForm

    list_display = (
        'username',
        'email',
        'tipo_cuenta',
        'is_staff',
        'is_active',
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    add_fieldsets = (
        (
            'Tipo de cuenta y acceso',
            {
                'description': (
                    'Elija Cliente y complete los datos del cliente, o Administrador bancario '
                    '(solo gestión en la API, sin ficha de cliente).'
                ),
                'fields': (
                    'rol',
                    'username',
                    'email',
                    'password1',
                    'password2',
                ),
            },
        ),
        (
            'Datos del cliente (obligatorios solo si el tipo es Cliente)',
            {
                'fields': (
                    'nombre_completo',
                    'numero_identificacion',
                    'telefono',
                    'direccion',
                    'fecha_nacimiento',
                ),
            },
        ),
    )

    def get_inlines(self, request, obj):
        if obj is None:
            return []
        if obj.is_staff or obj.is_superuser:
            return []
        return [ClienteInline]

    def tipo_cuenta(self, obj):
        if obj.is_superuser or obj.is_staff:
            return 'Administrador bancario'
        if Cliente.objects.filter(user=obj).exists():
            return 'Cliente'
        return 'Sin perfil de cliente'

    tipo_cuenta.short_description = 'Tipo de cuenta'

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        El admin llama form.save(commit=False) y luego save_model(obj.save()).
        Por eso la creación de Cliente y los grupos deben hacerse aquí, no solo
        en el if commit=True del formulario.
        """
        super().save_model(request, obj, form, change)
        if change or not isinstance(form, CrearUsuarioBancoForm):
            return
        cd = form.cleaned_data
        rol = cd.get('rol')
        Group.objects.get_or_create(name='cliente')
        Group.objects.get_or_create(name='administrador_bancario')
        obj.groups.clear()
        if rol == CrearUsuarioBancoForm.ROL_ADMIN:
            obj.groups.add(Group.objects.get(name='administrador_bancario'))
            return
        obj.groups.add(Group.objects.get(name='cliente'))
        if not Cliente.objects.filter(user=obj).exists():
            Cliente.objects.create(
                user=obj,
                nombre_completo=cd['nombre_completo'].strip(),
                numero_identificacion=cd['numero_identificacion'].strip(),
                email=cd['email'].strip(),
                telefono=cd['telefono'].strip(),
                direccion=cd['direccion'].strip(),
                fecha_nacimiento=cd['fecha_nacimiento'],
            )
