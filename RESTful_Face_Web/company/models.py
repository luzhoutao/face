from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
# utils
from datetime import datetime
import shutil
import os
from django.utils.dateparse import parse_duration
from django.utils import timezone
# service
from RESTful_Face_Web.settings import MEDIA_ROOT
# face feature
from service.settings import feature_dimension

# Create your models here.

class RandomSeed(models.Model):
    holder = models.OneToOneField(User, related_name="random_seed", on_delete=models.CASCADE)
    seed = models.CharField(max_length=50)


class App(models.Model):
    company = models.ForeignKey(User, related_name="apps", on_delete=models.CASCADE)
    appID = models.CharField(max_length=100, unique=True)

    app_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    update_time = models.DateTimeField(auto_now=True)

    def get_status(self):
        return 'live' if self.is_active else 'closed'

    def get_db_name(self):
        return self.company.first_name + self.app_name

    def get_update_time(self):
        return timezone.localtime(self.update_time)

    def delete(self, using=None, keep_parents=False):
        faces_path = os.path.join(MEDIA_ROOT, 'faces', str(self.appID))
        models_path = os.path.join(MEDIA_ROOT, 'classifier models', str(self.appID))
        if os.path.exists(faces_path):
            shutil.rmtree(faces_path)
        if os.path.exists(models_path):
            shutil.rmtree(models_path)
        super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        return self.app_name+'('+self.appID+')'

class Token2Token(models.Model):
    # every user has a token to generate token for API usage
    company = models.OneToOneField(User, on_delete=models.CASCADE)
    duration = models.DurationField() # new in Django1.8
    created_time = models.DateTimeField(auto_now_add=True)

    def get_duration(self):
        return self.duration.__str__()


def get_target_app(company, appID=None):
    """Find the target active app of company with the specified appID"""
    apps = App.objects.filter(company=company, is_active=True).all()
    if appID != None:
        apps = apps.filter(appID=appID)
    return None if len(apps)==0 else apps[0]


SERVICES = []

class Command(models.Model):
    company = models.ForeignKey(User, related_name="commands", on_delete=models.CASCADE)
    app = models.ForeignKey(App, related_name="commands", on_delete=models.CASCADE)
    serviceID = models.IntegerField()
    issue_time = models.DateTimeField(auto_now_add=True)

    arguments = models.CharField(max_length=1024, blank=True)
    results = models.CharField(max_length=1024, blank=True)

    def get_service_name(self):
        r = [service[1] for service in SERVICES if service[0]==self.serviceID]
        print(r)
        return r[0] if len(r) == 1 else 'Invalid serviceID !'

    def get_issue_time(self):
        return timezone.localtime(self.issue_time)

#################### Data For Company ###################

class Subject(models.Model):
    '''
    The class to represent a subject of a company.
    :param subjectID: generated automatically by the system
    :param name: assigned by the company itself. (should be unique)
    :param email: could be blank
    :param first_name: could be blank
    :param last_name: could be blank
    :param note: could be blank
    :param created_time, modified_time: self explanatory
    
    '''
    subjectID = models.CharField(max_length=50)
    appID = models.CharField(max_length=50)

    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    subject_name = models.CharField(max_length=50, validators=[RegexValidator(r'^[\w.@+-]+$')])
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.subject_name+'('+self.appID+'|'+self.subjectID+')'

    def get_faces_dir(self):
        return  "faces/%s/u%s/"%(self.appID, self.subjectID)

    def delete(self, using=None, keep_parents=False):
        path = os.path.join(MEDIA_ROOT, self.get_faces_dir())
        if os.path.exists(path):
            shutil.rmtree(path)
        super().delete(using=using, keep_parents=keep_parents)

    @staticmethod
    def generate_sqlite():
        return ['CREATE TABLE "company_person" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,'
                ' "userID" varchar(50) NOT NULL, "appID" varchar(50) NOT NULL, '
                '"created_time" datetime NOT NULL, "modified_time" datetime NOT NULL, '
                '"email" varchar(254) NOT NULL, "first_name" varchar(30) NOT NULL, '
                '"last_name" varchar(30) NOT NULL, "note" varchar(200) NOT NULL, "name" varchar(50) NOT NULL);', ]

    @staticmethod
    def generate_mysql():
        return ['''CREATE TABLE `company_subject` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `subjectID` varchar(50) NOT NULL,
  `appID` varchar(50) NOT NULL,
  `created_time` datetime NOT NULL,
  `modified_time` datetime NOT NULL,
  `subject_name` varchar(50) NOT NULL,
  `email` varchar(254) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `note` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1''', ]

def face_file_path(instance, filename):
    return instance.subject.get_faces_dir()+'{2}/{3}'.format(instance.subject.appID, instance.subject.subjectID, datetime.now().strftime("%y%m%d"), filename)

class Face(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='faces')
    image = models.ImageField(upload_to=face_file_path)
    created_time = models.DateField(auto_now_add=True)
    modified_time = models.DateField(auto_now=True)

    @staticmethod
    def generate_sqlite():
        return ['''CREATE TABLE "company_face" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "image" varchar(100) NOT NULL, "created_time" date NOT NULL, "modified_time" date NOT NULL, "person_id" integer NOT NULL REFERENCES "company_person" ("id"));''',
                '''CREATE INDEX "company_face_person_id_f7b922d6" ON "company_face" ("person_id");''', ]

    @staticmethod
    def generate_mysql():
        return ['''CREATE TABLE `company_face` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `image` varchar(100) NOT NULL,
  `created_time` date NOT NULL,
  `modified_time` date NOT NULL,
  `subject_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `company_face_subject_id_d11576ce_fk_company_subject_id` (`subject_id`),
  CONSTRAINT `company_face_subject_id_d11576ce_fk_company_subject_id` FOREIGN KEY (`subject_id`) REFERENCES `company_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1''', ]

    # override to also delete the file in storage
    # http://danceintech.blogspot.sg/2015/01/django-reminder-delete-file-when.html
    def delete(self, using=None, keep_parents=False):
        print('deleting')
        filename = self.image.path
        storage = self.image.storage
        super().delete(using, keep_parents)
        storage.delete(filename)

class FeatureTemplate(models.Model):
    feature_name = models.CharField(max_length=50)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='templates')

    data = models.CharField(max_length=20000, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('feature_name', 'subject'),)

    @staticmethod
    def generate_sqlite():
        return ['''CREATE TABLE "company_featuregallery" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(50) NOT NULL, "data" varchar(20000) NOT NULL, "created_time" datetime NOT NULL, "modified_time" datetime NOT NULL, "person_id" integer NOT NULL UNIQUE REFERENCES "company_person" ("id"));''']

    @staticmethod
    def generate_mysql():
        return ['''CREATE TABLE `company_featuretemplate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `feature_name` varchar(50) NOT NULL,
  `data` varchar(20000) NOT NULL,
  `created_time` datetime NOT NULL,
  `modified_time` datetime NOT NULL,
  `subject_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `company_featuretemplate_feature_name_subject_id_b1249808_uniq` (`feature_name`,`subject_id`),
  KEY `company_featuretempl_subject_id_d2d5f098_fk_company_s` (`subject_id`),
  CONSTRAINT `company_featuretempl_subject_id_d2d5f098_fk_company_s` FOREIGN KEY (`subject_id`) REFERENCES `company_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1''', ]

class Feature(models.Model):
    face = models.ForeignKey(Face, related_name='features', on_delete=models.CASCADE)
    data = models.CharField(max_length=20000) # use json dump
    feature_name = models.CharField(max_length=50) # the name of feature
    created_time = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_sqlite():
        return ['''CREATE TABLE "company_feature" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "data" varchar(2000) NOT NULL, "name" varchar(50) NOT NULL, "created_time" datetime NOT NULL, "face_id" integer NOT NULL UNIQUE REFERENCES "company_face" ("id"));''', ]

    @staticmethod
    def generate_mysql():
        return ['''CREATE TABLE `company_feature` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `data` varchar(20000) NOT NULL,
  `feature_name` varchar(50) NOT NULL,
  `created_time` datetime NOT NULL,
  `face_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `company_feature_face_id_a66f0874_fk_company_face_id` (`face_id`),
  CONSTRAINT `company_feature_face_id_a66f0874_fk_company_face_id` FOREIGN KEY (`face_id`) REFERENCES `company_face` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1''', ]


def classifier_file_path(instance, filename):
    return 'classifier models/{0}/{1}/{2}/{3}'.format(instance.appID, instance.classifier_name, instance.feature_name, filename)


class ClassifierModel(models.Model):
    appID = models.CharField(max_length=50)
    classifier_name = models.CharField(max_length=50)
    feature_name = models.CharField(max_length=50)
    parameter_file = models.FileField(upload_to=classifier_file_path)
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    #additional_data = models.FileField(upload_to=classifier_file_path, blank=True)

    @staticmethod
    def generate_sqlite():
        return ['''CREATE TABLE "company_classifiermodel" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "appID" varchar(50) NOT NULL, "name" varchar(50) NOT NULL, "feature_name" varchar(50) NOT NULL, "parameter_file" varchar(100) NOT NULL, "created_time" datetime NOT NULL, "modified_time" datetime NOT NULL);''',]

    @staticmethod
    def generate_mysql():
        return ['''CREATE TABLE `company_classifiermodel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `appID` varchar(50) NOT NULL,
  `classifier_name` varchar(50) NOT NULL,
  `feature_name` varchar(50) NOT NULL,
  `parameter_file` varchar(100) NOT NULL,
  `created_time` datetime NOT NULL,
  `modified_time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1''', ]
