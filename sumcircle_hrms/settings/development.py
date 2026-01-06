from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]  # or localhost

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:8000",
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'nitin.projecttesting@gmail.com'
EMAIL_HOST_PASSWORD = 'gsugwcptwetoptii'
EMAIL_USE_TLS = True

DEFAULT_FROM_MAIL = 'nitin.projecttesting@gmail.com'
ADMIN_MAIL = 'nitin.projecttesting@gmail.com'