from django import forms
from django.core.validators import RegexValidator


class LoginForm(forms.Form):
    """ User login form: userid and encoded password """
    option = forms.ChoiceField(choices=(('default', 'Default'), ('ivle', 'NUS IVLE')), required=False)
    username = forms.CharField(max_length=30, label='User Name')
    password = forms.CharField(widget=forms.PasswordInput())


class DataForm(forms.Form):
    """ data usually is dict, token is AuthToken fetch from IVLE """
    data = forms.CharField()
    token = forms.CharField(max_length=500, label='Auth Token', required=False)
    group = forms.IntegerField(label='Group ID', required=False)
    module = forms.CharField(label='Module ID', required=False)
    # cg = forms.BooleanField(label='class or guest', required=False)
    lt = forms.BooleanField(label='lecture or tutorial', required=False)
    owner = forms.CharField(label='Owner', required=False)
    time_id = forms.IntegerField(label='Time ID', required=False)


class ImgForm(forms.Form):
    """ Provide img with data """
    image = forms.ImageField()
    data = forms.CharField(required=False, label='Data (optional)')
    group = forms.IntegerField(label='Group ID', required=False)
    module = forms.CharField(label='Module ID', required=False)
    lt = forms.BooleanField(label='lecture or tutorial', required=False)


class ModuleForm(forms.Form):
    """ create a new module form """
    code = forms.CharField(label='Module Code', max_length=50)
    name = forms.CharField(label='Module Name', max_length=100)
    year = forms.CharField(label='Academic Year', max_length=20, required=False)
    semester = forms.CharField(label='Semester', max_length=100, required=False)


class StudentForm(forms.Form):
    """ add student form """
    module = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(label='Name (unique)', max_length=50, validators=[RegexValidator(r'^[\w.@+-]+$')])
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    note = forms.CharField(max_length=200, required=False)

    # def __init__(self, custom_choices=None, *args, **kwargs):
    #     super(StudentForm, self).__init__(*args, **kwargs)
    #     if custom_choices:
    #         self.fields['module'].choices = custom_choices