import os

API_KEY = None
with open(os.path.join('.secrets', 'api_key.txt'), encoding='utf-8') as file:
    API_KEY = file.readline()
STROM_ID = 2839
