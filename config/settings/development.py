"""
Development settings for Restaurant Booking project.
"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# SQLite database for development  
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Static files for development (disable WhiteNoise compression)
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"