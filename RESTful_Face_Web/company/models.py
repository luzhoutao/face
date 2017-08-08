from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Create your models here.

class RandomSeed(models.Model):
    holder = models.OneToOneField(User, related_name="random_seed", on_delete=models.CASCADE)
    seed = models.CharField(max_length=50)

class Person(models.Model):
    '''
    The class to represent a person of a company.
    :param userID: generated automatically by the system
    :param name: assigned by the company itself. (should be unique)
    :param email: could be blank
    :param first_name: could be blank
    :param last_name: could be blank
    :param note: could be blank
    :param companyID: associate with the companyID (will be decaperated)
    :param created_time, modified_time: self explanatory
    
    '''
    userID = models.CharField(max_length=50)
    companyID = models.CharField(max_length=50)

    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=50, unique=True, validators=[RegexValidator(r'^[\w.@+-]+$')])
    email = models.EmailField(blank=True, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=200, blank=True)
