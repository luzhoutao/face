# retrieve project path settings
from RESTful_Face_Web import settings
# database connections
from django.db import connections
from company.models import Person
# system operation
import os
# logging
import logging, traceback

log = logging.getLogger(__name__)

DB_SETTINGS_BASE_DIR = os.path.join(settings.BASE_DIR, 'company/utils/database_settings')

def create_sqlite_database(name):
    name = str(name)
    filename = os.path.join(settings.BASE_DIR, 'db_'+name+'.sqlite3')

    # tell Django there is a new database
    setting_str = '''connections.databases['%s'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': '%s',
}'''% (name, filename)
    exec(setting_str)
    save_db_settings_to_file(setting_str, name)

    # create database file
    file = open(filename, 'w+')
    file.close()

    # initialize the database file
    import sqlite3

    conn = sqlite3.connect(filename)
    conn.execute(Person.generate_sqlite())
    conn.close()
    
    log.info("Created sqlite database %s and initialize a table 'Person'!"%(name))

def create_mysql_database(name):
    name = str(name)

    # tell Django there is a new mysql database
    setting_str = '''connections.databases['%s'] = {
    'ENGINE': 'django.db.backends.mysql',
    'USER': '%s',
    'PASSWORD': '%s',
    'NAME': 'company%s',
    'HOST': '%s',
    'PORT': '3306' ,
}'''% (name, settings.MYSQL_USER, settings.MYSQL_PASSWORD, name, settings.MYSQL_HOST)
    exec(setting_str)
    save_db_settings_to_file(setting_str, name)

    # create database
    import pymysql
    conn = pymysql.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, password = settings.MYSQL_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("create database company%s"%(name))
    conn.commit()
    conn.close()
    
    # initializer database
    conn = pymysql.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, password = settings.MYSQL_PASSWORD, db='company'+name)
    cursor = conn.cursor()
    cursor.execute(Person.generate_mysql())
    conn.commit()
    conn.close()
    
    log.info("Created mysql database %s and initialize a table 'Person'!"%(name))

def save_db_settings_to_file(setting_str, name):
    filename = os.path.join(DB_SETTINGS_BASE_DIR, name+'.dbconf')
    file = open(filename, 'w+')
    file.write(setting_str)
    file.close()

    log.info('Database settings file %s.dbconf saved!'%(name))

def drop_mysql_database(name):
    # delete setting files
    try:
        os.remove(os.path.join(DB_SETTINGS_BASE_DIR, name+'.dbconf'))
        log.info("DB setting file %s.dbconf is moved!" % (name))
    except FileNotFoundError:
        log.warning("DB setting file %s.dbconf has already been moved!" % (name))
        log.error(traceback.format_exc())
    # delete database
    import pymysql
    conn = pymysql.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD)
    cursor = conn.cursor()
    cursor.execute('drop database company%s;'%(name))
    conn.commit()
    conn.close()
    log.info("Database company%s has been dropped !" % (name))
