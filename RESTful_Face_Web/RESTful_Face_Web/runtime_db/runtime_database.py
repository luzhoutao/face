# retrieve project path settings
# database connections
from django.db import connections
# system operation
import os
# logging
import logging, traceback
log = logging.getLogger(__name__)
# abstract class
from abc import ABCMeta, abstractmethod

from RESTful_Face_Web import settings

# database manager to create on the fly and initialize it !
# https://stackoverflow.com/questions/6585373/django-multiple-and-dynamic-databases
class BaseDBManager():
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_database(self, name):
        raise NotImplementedError

    @abstractmethod
    def create_table(self, db_name, Model, table_name):
        raise  NotImplementedError

    @abstractmethod
    def drop_database(self, name):
        raise NotImplementedError


class SQLiteManager(BaseDBManager):

    def create_database(self, name):
        from RESTful_Face_Web import settings
        name = str(name)
        filename = os.path.join(settings.BASE_DIR, 'db_'+name+'.sqlite3')

        # tell Django there is a new database
        setting_str = '''settings.DATABASES['%s'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': '%s',
}'''% (name, filename)
        exec(setting_str)
        save_db_settings_to_file(setting_str, name)

        # create database file
        file = open(filename, 'w+')
        file.close()

    def create_table(self, db_name, Model, table_name):
        # initialize the database file
        import sqlite3
        from RESTful_Face_Web import settings

        filename = os.path.join(settings.BASE_DIR, 'db_'+db_name+'.sqlite3')
        conn = sqlite3.connect(filename)
        [conn.execute(sql) for sql in Model.generate_sqlite()]
        conn.close()

        log.info("Created sqlite database %s and initialize a table '%s'!"%(db_name, table_name))

    def drop_database(self, name):
        try:
            connections.databases.pop(name)
            os.remove(os.path.join(settings.DB_SETTINGS_BASE_DIR, name + '.dbconf'))
            os.remove(os.path.join(settings.BASE_DIR, 'db_' + name + '.sqlite3'))
            log.info("Database %s is moved!" % (name))

        except FileNotFoundError:
            log.warning("DB %s has already been moved!" % (name))
            log.error(traceback.format_exc())
        except KeyError:
            log.warning("Database %s is not in use!"% (name))

class MySQLManager(BaseDBManager):

    def create_database(self, name):
        from RESTful_Face_Web import settings

        name = str(name)

        # tell Django there is a new mysql database
        setting_str = '''settings.DATABASES['%s'] = {
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
        conn = pymysql.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("create database company%s" % (name))
        conn.commit()
        conn.close()

    def create_table(self, db_name, Model, table_name):
        import pymysql
        from RESTful_Face_Web import settings
        # initializer database
        conn = pymysql.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD,
                               db='company' + db_name)
        cursor = conn.cursor()
        [cursor.execute(sql) for sql in Model.generate_mysql()]
        conn.commit()
        conn.close()

        log.info("Created mysql database %s and initialize a table '%s'!" % (db_name, table_name))

    def drop_database(self, name):
        from RESTful_Face_Web import settings
        print("dropping database, ", name)
        # delete setting files
        try:
            connections.databases.pop(name)
            os.remove(os.path.join(settings.DB_SETTINGS_BASE_DIR, name + '.dbconf'))
            log.info("DB setting file %s.dbconf is moved!" % (name))
        except FileNotFoundError:
            log.warning("DB setting file %s.dbconf has already been moved!" % (name))
            log.error(traceback.format_exc())
        except KeyError:
            log.warning('Database %s is not in use!' % (name))

        # delete database
        import pymysql
        conn = pymysql.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD)
        cursor = conn.cursor()
        cursor.execute('drop database company%s;' % (name))
        conn.commit()
        conn.close()
        log.info("Database company%s has been dropped !" % (name))

def save_db_settings_to_file(setting_str, name):
    from RESTful_Face_Web import settings
    filename = os.path.join(settings.DB_SETTINGS_BASE_DIR, name+'.dbconf')
    file = open(filename, 'w+')
    file.write(setting_str)
    file.close()

    log.info('Database settings file %s.dbconf saved!'%(name))
