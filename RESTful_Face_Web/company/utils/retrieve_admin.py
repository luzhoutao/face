from django.contrib.auth.models import User
from RESTful_Face_Web.settings import ADMIN_NAME

def get_admin():
    '''
    :return: get the admin user of this project
    '''
    return User.objects.get(username=ADMIN_NAME)