import facebook
import requests
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()
# this will return false if not run locally, but it doesn't matter

curdate = datetime.now().strftime('%Y-%m-%d')
params = {'start_period': curdate, 'end_period': curdate}
headers = {'x-ibm-client-id': os.getenv('BOT_API_KEY'),
		   'accept': "application/json"}

r = requests.get('https://apigw1.bot.or.th//bot/public/Stat-ReferenceRate/v2/DAILY_REF_RATE/',
				 params=params, headers=headers)
tmp = r.json()['result']['data']['data_detail'][0]
if tmp['rate']:
	# updated
	message = ("เรทเฉลี่ยค่าเงินบาท (THBREF) วันนี้\n\n"
			   "{:0.3f} บาท ต่อ 1 ดอลลาร์ สรอ.\n\n"
			   "หมายเหตุ: THBREF = อัตราแลกเปลี่ยนถัวเฉลี่ยถ่วงน้ำหนักระหว่างธนาคาร").format(float(tmp['rate']))
	graph = facebook.GraphAPI(access_token=os.getenv('FACEBOOK_ACCESS_TOKEN'), version='3.1')
	api_request = graph.put_object(
		parent_object='me', # page ID
		connection_name='feed',
		message=message,
	)
else:
    print("วันนี้ตลาดปิดทำการ")