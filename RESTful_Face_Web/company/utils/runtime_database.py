from RESTful_Face_Web import settings
from django.db import connections
import os

DB_SETTINGS_BASE_DIR = os.path.join(settings.BASE_DIR, 'company/utils/database_settings')

def create_database(name):
    name = str(name)
    filename = os.path.join(settings.BASE_DIR, 'db_'+name+'.sqlite3')

    # tell Django there is a new database TODO
    db = {}
    db['ENGINE'] = 'django.db.backends.sqlite3'
    db['NAME'] = filename
    connections.databases[name] = db
    db['id'] = name
    save_db_settings_to_file(db)

    # create database file  TODO
    file = open(filename, 'w+')
    file.close()

    create_person_table = 'CREATE TABLE "company_person" ' \
                          '("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "userID" varchar(50) NOT NULL, ' \
                          '"companyID" varchar(50) NOT NULL, "created_time" datetime NOT NULL, "modified_time" datetime NOT NULL, ' \
                          '"name" varchar(50) NOT NULL UNIQUE, "first_name" varchar(30) NOT NULL, "last_name" varchar(30) NOT NULL, ' \
                          '"note" varchar(200) NOT NULL, "email" varchar(254) NOT NULL);'

    # initialize the database file TODO
    import sqlite3

    conn = sqlite3.connect(filename)
    conn.execute(create_person_table)
    conn.close()

def save_db_settings_to_file(db):
    filename = os.path.join(DB_SETTINGS_BASE_DIR, db['id']+'.dbconf')
    setting_str = '''connections.databases['%s'] = {
    'ENGINE': '%s',
    'NAME': '%s',
}'''% (db['id'], db['ENGINE'], db['NAME'])
    print('setting_str:', setting_str)

    file = open(filename, 'w+')
    file.write(setting_str)
    file.close()