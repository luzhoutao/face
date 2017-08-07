from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class RandomSeed(models.Model):
    holder = models.OneToOneField(User, related_name="random_seed", on_delete=models.CASCADE)
    seed = models.CharField(max_length=50)

def get_seed_of_user(user):
    try:
        seed = user.random_seed
    except RandomSeed.DoesNotExist:
        seed = RandomSeed.objects.create(holder=user, seed='1')
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
        
