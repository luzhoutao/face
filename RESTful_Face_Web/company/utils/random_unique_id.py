from math import pow
import random
from ..models import RandomSeed

def generate_unique_id(user):
    # https://en.wikipedia.org/wiki/Linear_congruential_generator
    module = pow(2, 32)
    a = 1664525
    c = 1013904223
    seed = get_seed_of_user(user)

    newseed = int((a * seed + c) % module)
    update_seed_of_user(user, newseed)

    return str(newseed).zfill(10)

def get_seed_of_user(user):
    try:
        seed = user.random_seed
    except RandomSeed.DoesNotExist:
        seed = RandomSeed.objects.create(holder=user, seed=str(int(random.SystemRandom().random()*100)))
        seed.save()
    return int(seed.seed)

def update_seed_of_user(user, newseed):
    try:
        seed = user.random_seed
        seed.seed = str(newseed)
        seed.save()
    except RandomSeed.DoesNotExist:
        seed = RandomSeed.objects.create(holder=user, seed=str(newseed))
        seed.save()
