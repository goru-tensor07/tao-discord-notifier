import os
import time
from datetime import datetime, timedelta, timezone

import requests, json
# import matplotlib.pyplot as plt


#parameters
#allowed days or hours
scale = "days"
number_of_points = 30

try:
    from dotenv import load_dotenv
except ImportError:
    # dotenv is optional - script will work with environment variables only
    load_dotenv = None

# --- Environment configuration ---

# Load .env file if python-dotenv is available
if load_dotenv is not None:
    load_dotenv()

api_key=os.environ.get("TAOSTATS_API_KEY")




coldkey = "5G3xHmDRz9yWDS9tnznWTVnyhCvLZiLUUbqFbRNEreGSCYgD"


# Example: Get data from last 24 hours

count = 200
network = "Finney"
page =1
limit = 50
#get current block
url = f"https://api.taostats.io/api/account/latest/v1?address={coldkey}&network={network}&page={page}&limit={limit}"

headers = {"accept": "application/json", "authorization":api_key}
response = requests.get(url, headers=headers)
resJson = json.loads(response.text)
data = resJson['data']
address = data[0]
balance_staked = address.get('balance_staked')
print(balance_staked)

