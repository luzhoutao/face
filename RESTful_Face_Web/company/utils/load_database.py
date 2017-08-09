from django.db import connections
import os
from .runtime_database import DB_SETTINGS_BASE_DIR

for filename in os.listdir(DB_SETTINGS_BASE_DIR):
    if 'dbconf' not in filename:
        continue
    path = os.path.join(DB_SETTINGS_BASE_DIR, filename)
    f = open(path)
    db_settings = f.read()
    f.close()
    exec(db_settings)
