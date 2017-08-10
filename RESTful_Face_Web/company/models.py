from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
# utils
from datetime import datetime

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
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=200, blank=True)

    @staticmethod
    def generate_sqlite():
        return ['CREATE TABLE "company_person" ' \
                          '("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "userID" varchar(50) NOT NULL, ' \
                          '"companyID" varchar(50) NOT NULL, "created_time" datetime NOT NULL, "modified_time" datetime NOT NULL, ' \
                          '"name" varchar(50) NOT NULL UNIQUE, "first_name" varchar(30) NOT NULL, "last_name" varchar(30) NOT NULL, ' \
                          '"note" varchar(200) NOT NULL, "email" varchar(254) NOT NULL);', ]

    @staticmethod
    def generate_mysql():
        return ['''CREATE TABLE `company_person` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userID` varchar(50) NOT NULL,
  `companyID` varchar(50) NOT NULL,
  `created_time` datetime NOT NULL,
  `modified_time` datetime NOT NULL,
  `name` varchar(50) NOT NULL,
  `email` varchar(254) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `note` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1
''', ]

def face_file_path(instance, filename):
    return 'faces/user_{0}/{1}/{2}'.format(instance.person.userID, datetime.now().strftime("%y%m%d"), filename)

class Face(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='faces')
    feature = models.CharField(max_length=10240, blank=True)
    image = models.ImageField(blank=True, null=True, upload_to=face_file_path)
    created_time = models.DateField(auto_now_add=True)
    modified_time = models.DateField(auto_now=True)

    @staticmethod
    def generate_sqlite():
        return ['''CREATE TABLE "company_face" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "created_time" date NOT NULL, "modified_time" date NOT NULL, "person_id" integer NOT NULL REFERENCES "company_person" ("id"), "image" varchar(100) NULL, "feature" varchar(10240) NOT NULL);''',
                'CREATE INDEX "company_face_person_id_f7b922d6" ON "company_face" ("person_id");', ]

    # override to also delete the file in storage
    # http://danceintech.blogspot.sg/2015/01/django-reminder-delete-file-when.html
    def delete(self, using=None, keep_parents=False):
        filename = self.image.path
        storage = self.image.storage
        super().delete(using, keep_parents)
        storage.delete(filename)