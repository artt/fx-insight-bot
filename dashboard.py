import facebook
import requests
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance, ImageFilter, ImageFont, ImageDraw
import re
import os
import io
import sys

from dotenv import load_dotenv
load_dotenv()

def get_thbref(date_start, date_end):
    params = {'start_period': date_start.strftime('%Y-%m-%d'), 'end_period': date_end.strftime('%Y-%m-%d')}
    headers = {'x-ibm-client-id': os.getenv('BOT_API_KEY'),
               'accept': "application/json"}
    r = requests.get('https://apigw1.bot.or.th/bot/public/Stat-ReferenceRate/v2/DAILY_REF_RATE/',
                     params=params,
                     headers=headers)
    # get reverse-sorted data, so pick the first one
    tmp = r.json()['result']['data']['data_detail'][0]['rate']
    if tmp != '':
        return float(tmp)
    return float('nan')
    
def get_thbref_before(d):
    return get_thbref(d - timedelta(days=7), d - timedelta(days=1))



# THBREF

curdate = datetime.now()
var_thb = get_thbref(curdate, curdate)

# if var_thb != var_thb:
#     print('No data for today.')
#     os.system('''echo "RUN_RESULT=notrade" >> $GITHUB_ENV''')
#     sys.exit(0)

tmp_endlastday = get_thbref_before(curdate)
tmp_endlastmonth = get_thbref_before(curdate.replace(day=1))
tmp_endlastyear = get_thbref_before(curdate.replace(month=1, day=1))
var_thb_1d = var_thb - tmp_endlastday
var_thb_mtd = var_thb - tmp_endlastmonth
var_thb_ytd = var_thb - tmp_endlastyear


# ThaiBMA

r = requests.get('https://eagle.thaibma.or.th/catcher/dashboard/nonresidentnetflow', verify=False)
tmp = r.json()[0]

bmadate = tmp['_dailyNetFlow'][0]['DayMonth']
if (curdate.date() != datetime.strptime(bmadate[:10], '%Y-%m-%d').date()):
    print('No BMA data for today yet.')
    os.system('''echo "RUN_RESULT=nothaibma" >> $GITHUB_ENV''')
    sys.exit(0)

var_bond = sum(map(lambda x: x['TotalNetValue'], tmp['_dailyNetFlow']))
var_bond_mtd = tmp['_monthNetFlow'][0]['TotalNetValue']
var_bond_ytd = tmp['_yearNetFlow'][0]['TotalNetValue']


# SETTrade

r = requests.get('https://www.settrade.com/C13_InvestorType.jsp?market=SET')
tmp = r.content.decode('cp874')

setdate = re.findall("สรุปการซื้อขาย ณ วันที่ (\d+)", tmp, re.MULTILINE | re.DOTALL)
if (int(setdate[0]) != curdate.day):
    print("No SET data for today yet.")
    os.system('''echo "RUN_RESULT=noset" >> $GITHUB_ENV''')
    sys.exit(0)

pattern = "นักลงทุนต่างประเทศ(?:.*?<td){5}.*?>([^<]+)"
m = re.findall(pattern, tmp, re.MULTILINE | re.DOTALL)
[var_stock, var_stock_mtd, var_stock_ytd] = list(map(lambda x: float(x.replace(',', '')), m))


# Create photo to be posted

bkg_img = Image.open("resources/bkg-01.png")
b = bkg_img.convert('L').resize((1, 1)).getpixel((0, 0)) # get average brightness
bkg_img = bkg_img.filter(ImageFilter.GaussianBlur(3))
enhancer = ImageEnhance.Brightness(bkg_img)
bkg = enhancer.enhance(40/b)
template = Image.open("resources/template.png")
bkg.paste(template, (0, 0), template)

font_thb = ImageFont.truetype(font='resources/DB Helvethaica X Bd v3.2.ttf', size=130, index=0, encoding='')
font_flow = ImageFont.truetype(font='resources/DB Helvethaica X Bd v3.2.ttf', size=106, index=0, encoding='')
font_date = ImageFont.truetype(font='resources/DB Helvethaica X Bd v3.2.ttf', size=36, index=0, encoding='')
font_change = ImageFont.truetype(font='resources/DB Helvethaica X v3.2.ttf', size=48, index=0, encoding='')

def get_color(v):
    if v >= 0:
        return "#01b651"
    return "#cc1111"

def draw_change_text(draw_obj, pos, v, font=font_change, formatter='{:+.2f}'):
    draw_obj.text(pos, formatter.format(v), font=font, anchor="ms", fill=get_color(v))

tmp = bkg.copy()
draw = ImageDraw.Draw(tmp)

# place texts

draw.text((877, 160), curdate.strftime('%d %b %Y'), font=font_date, anchor="rs", fill="white")
draw.text((280, 320), '{:.3f}'.format(var_thb), font=font_thb, anchor="ms", fill="white")

draw_change_text(draw, (565, 320), var_thb_1d)
draw_change_text(draw, (695, 320), var_thb_mtd)
draw_change_text(draw, (825, 320), var_thb_ytd)

draw_change_text(draw, (280, 590), var_stock, font=font_flow, formatter='{:+,.0f}')
draw_change_text(draw, (280, 680), var_stock_mtd, formatter='{:+,.0f}')
draw_change_text(draw, (280, 780), var_stock_ytd, formatter='{:+,.0f}')

draw_change_text(draw, (680, 590), var_bond, font=font_flow, formatter='{:+,.0f}')
draw_change_text(draw, (680, 680), var_bond_mtd, formatter='{:+,.0f}')
draw_change_text(draw, (680, 780), var_bond_ytd, formatter='{:+,.0f}')

img_byte_arr = io.BytesIO()
tmp.save(img_byte_arr, format='png')
img_byte_arr = img_byte_arr.getvalue()

msg = (("{}\n\n"
        "เรทเฉลี่ยค่าเงินบาท (THBREF) {:0.3f} บาท ต่อ 1 ดอลลาร์ สรอ.\n\n"
        "ต่างชาติ{}หุ้นสุทธิ {:,.0f} ล้านบาท {}บอนด์สุทธิ {:,.0f} ล้านบาท")
       .format(curdate.strftime('%d/%m/%Y'),
               var_thb,
               'ขาย' if var_stock < 0 else 'ซื้อ', abs(var_stock),
               'ขาย' if var_bond < 0 else 'ซื้อ', abs(var_bond)))

album_id = os.getenv('ALBUM_ID')
if not album_id:
	album_id = 'me'
graph = facebook.GraphAPI(access_token=os.getenv('FACEBOOK_ACCESS_TOKEN'), version='3.1')
api_request = graph.put_photo(image=img_byte_arr,
                message=msg, album_path=album_id + "/photos")