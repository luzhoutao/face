from math import pow
from django.contrib.auth.models import User
from .models import get_seed_of_user, update_seed_of_user

def generate_unique_id(user):
    admin = User.objects.get(username='admin')

    # https://en.wikipedia.org/wiki/Linear_congruential_generator
    module = pow(2, 32)
    a = 1664525
    c = 1013904223
    seed = get_seed_of_user(admin)

    newseed = int((a * seed + c) % module)
    update_seed_of_user(admin, newseed)

    return str(newseed).zfill(10)
    
