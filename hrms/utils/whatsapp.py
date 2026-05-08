# import requests
# from django.conf import settings


# def send_whatsapp_message(to_number, message):

#     url = f"https://graph.facebook.com/v23.0/{settings.WA_PHONE_NUMBER_ID}/messages"

#     headers = {
#         "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "messaging_product": "whatsapp",
#         "to": to_number,
#         "type": "template",
#         "template": {
#             "name": "birthday_wish",
#             "language": {
#                 "code": "en"
#             }
#         }
#     }

#     response = requests.post(
#         url,
#         headers=headers,
#         json=payload
#     )

#     return response.json()