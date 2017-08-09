from django.db import connections
from RESTful_Face_Web import settings
import os
from RESTful_Face_Web.settings import DB_SETTINGS_BASE_DIR

for filename in os.listdir(DB_SETTINGS_BASE_DIR):
    if 'dbconf' not in filename:
        continue
    path = os.path.join(DB_SETTINGS_BASE_DIR, filename)
    f = open(path)
    db_settings = f.read()
    f.close()
    exec(db_settings)