from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from banking.models import Cliente

User = get_user_model()


class CrearUsuarioBancoForm(UserCreationForm):
    """Formulario de alta en admin: elige rol Cliente o Administrador bancario."""

    ROL_ADMIN = 'administrador_bancario'
    ROL_CLIENTE = 'cliente'

    rol = forms.ChoiceField(
        label='Tipo de cuenta',
        choices=[
            (ROL_CLIENTE, 'Cliente'),
            (ROL_ADMIN, 'Administrador bancario'),
        ],
        initial=ROL_CLIENTE,
        help_text='Cliente: acceso a sus cuentas. Administrador: gestión completa en la API.',
    )
    email = forms.EmailField(label='Correo electrónico', required=True)
    nombre_completo = forms.CharField(label='Nombre completo', required=False)
    numero_identificacion = forms.CharField(label='Número de identificación', required=False)
    telefono = forms.CharField(label='Teléfono', required=False)
    direccion = forms.CharField(
        label='Dirección',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
    fecha_nacimiento = forms.DateField(
        label='Fecha de nacimiento',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo.')
        if Cliente.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo ya está registrado como cliente.')
        return email

    def clean(self):
        cleaned = super().clean()
        rol = cleaned.get('rol')
        if rol != self.ROL_CLIENTE:
            return cleaned
        req = {
            'nombre_completo': 'Nombre completo',
            'numero_identificacion': 'Número de identificación',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'fecha_nacimiento': 'Fecha de nacimiento',
        }
        errores = {}
        for key, etiqueta in req.items():
            v = cleaned.get(key)
            if v is None or (isinstance(v, str) and not str(v).strip()):
                errores[key] = f'{etiqueta} es obligatorio para el rol Cliente.'
        if errores:
            raise forms.ValidationError(errores)
        doc = cleaned['numero_identificacion'].strip()
        if Cliente.objects.filter(numero_identificacion=doc).exists():
            raise forms.ValidationError(
                {'numero_identificacion': 'Ya existe un cliente con este número de identificación.'}
            )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        rol = self.cleaned_data['rol']
        user.is_staff = rol == self.ROL_ADMIN
        user.is_superuser = False
        if commit:
            user.save()
            Group.objects.get_or_create(name='cliente')
            Group.objects.get_or_create(name='administrador_bancario')
            user.groups.clear()
            if rol == self.ROL_ADMIN:
                user.groups.add(Group.objects.get(name='administrador_bancario'))
            else:
                user.groups.add(Group.objects.get(name='cliente'))
                Cliente.objects.create(
                    user=user,
                    nombre_completo=self.cleaned_data['nombre_completo'].strip(),
                    numero_identificacion=self.cleaned_data['numero_identificacion'].strip(),
                    email=self.cleaned_data['email'].strip(),
                    telefono=self.cleaned_data['telefono'].strip(),
                    direccion=self.cleaned_data['direccion'].strip(),
                    fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
                )
        return user
