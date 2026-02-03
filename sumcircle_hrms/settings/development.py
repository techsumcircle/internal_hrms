from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]  # or localhost

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:8000",
]

#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' # tells django to use smtp 
#EMAIL_HOST = 'smtp.gmail.com' #the mail server
#EMAIL_PORT = 587 # ye email ka port hai TLS, 465 SSL ka or , 25 old insecure
#EMAIL_HOST_USER = 'Saroj@sumcircle.com' # isi se mail jayega
#EMAIL_HOST_PASSWORD = '' # ye mail ka host password kyuki gmail ka normal password kaam nahi karta hume App password banana padta hai 
#EMAIL_USE_TLS = True # ye encreaption channel hai jisme data safe rahega

#DEFAULT_FROM_MAIL = 'Saroj@sumcircle.com' # Agar kahi explicit sender na diya ho to ye mail default sender hota hai 
#ADMIN_MAIL = 'Saroj@sumcircle.com' # ye admin ko hi notifications bhejne ke liye or alerts, error reports, contact form etc.



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'sarojsingh10100@gmail.com'
EMAIL_HOST_PASSWORD = 'cgco glzs xkgk fxwo'
EMAIL_USE_TLS = True

DEFAULT_FROM_MAIL = 'sarojsingh10100@gmail.com'
ADMIN_MAIL = 'sarojsingh10100@gmail.com'


VASBAY_USERNAME = "726f756e64657273"
VASBAY_API_KEY = "6098900e0c16780e983172deadd37030"
VASBAY_SENDER_ID = "CTLIND"
VASBAY_ENTITY_ID = "1701176951994290667"
VASBAY_CONTENT_ID = "1707176966994911647"
VASBAY_API_URL = "http://vasbay.com/webservice/smsSimpleApi.php"

## Vasbay SMS configurations
#VASBAY_USERNAME = "616c6c696e6172656e61" # SMS provider (VASBAY) ka username and Ye encoded / system-generated hota hai
#VASBAY_API_KEY = "75c93a19328783d9cbdcafaabd6b7ae7" #ye secret key hai jo ye confirm karta hia ki sms isi app se jaa rha hai ** isko public repo me nahi dale **
#VASBAY_SENDER_ID = "sumcircle" # SMS ka sender name me yahi dikhega
#VASBAY_ENTITY_ID = "1701175154157256238" ## India DLT system ka company registration ID ** India DLT system ka company registration ID**
#VASBAY_CONTENT_ID = "1707175187773974121" # SMS template ka ID ** ye message ka content pehle approve hone me use hota hai **
#VASBAY_API_URL = "http://vasbay.com/webservice/smsSimpleApi.php" # ye actual API endpoint hai yahi request jati hai SMS bhejne ke liye





#USER ACTION
#   ↓
#Django
#   ↓
#Email Config → Gmail SMTP → Email
#   ↓
#SMS Config → Vasbay API → SMS


#Common Mistakes (Very important)

#Gmail password directly use karna
#API keys GitHub pe push kar dena
#TLS false rakhna
# Comma laga dena string ke end me