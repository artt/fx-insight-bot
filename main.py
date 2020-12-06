import os
import requests

print("Hi there!")

curdate = '2020-12-04'
# curdate = datetime.now().strftime('%Y-%m-%d')
params = {'start_period': curdate, 'end_period': curdate}
headers = {'x-ibm-client-id': os.environ['BOT_API_KEY'],
           'accept': "application/json"}

r = requests.get('https://apigw1.bot.or.th//bot/public/Stat-ReferenceRate/v2/DAILY_REF_RATE/',
                 params=params, headers=headers)
tmp = r.json()['result']['data']['data_detail'][0]
print(tmp)
