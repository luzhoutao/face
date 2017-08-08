from django.contrib.auth.models import User

def get_admin():
    return User.objects.get(username='admin')