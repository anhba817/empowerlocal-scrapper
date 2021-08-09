import requests, json

from datetime import datetime
import argparse
import os, sys, calendar, csv

import gspread
from oauth2client.service_account import ServiceAccountCredentials

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

def parse_args(args):
    parser = argparse.ArgumentParser(description='Scrap data from mailchimp.')
    parser.add_argument("-m", "--month", type=int, help="Month")
    parser.add_argument("-y", "--year", type=int, help="Year")
    return parser.parse_args(args)

arguments = parse_args(sys.argv[1:])

month = arguments.month
year = arguments.year
today = datetime.today()
if not month:
    month = today.month - 1 if today.month != 1 else 12
if not year:
    year = today.year if today.month != 1 else today.year - 1

startDate = datetime(year, month, 1, 0, 0, 0)
last_day_in_month = calendar.monthrange(year, month)[1]
stopDate = datetime(year, month, last_day_in_month, 23, 59, 59)

since_date = startDate.strftime("%Y-%m-%d")
until_date = stopDate.strftime("%Y-%m-%d")

f = open(FILE_DIRECTORY + '/facebook.json', 'r')
facebook_auth = json.load(f)
f.close()

print("EXPORTING DATA FROM FACEBOOK ADS...")
url = "https://graph.facebook.com/v11.0/act_%s/insights" % (facebook_auth["ad_account"])

params = dict(
    level="ad",
    time_range="{'since':'%s', 'until':'%s'}" % (since_date, until_date),
    time_increment=1,
    fields="campaign_name,adset_name,ad_name,reach,impressions,inline_post_engagement,clicks,account_currency,cpc,ctr,frequency",
    access_token=facebook_auth["user"]["long_token"],
    sort="date_start_descending"
)

resp = requests.get(url=url, params=params)
data = []

data += (resp.json()["data"])

while "next" in resp.json()["paging"]:
    next_url = resp.json()["paging"]["next"]
    resp = requests.get(url=next_url)
    data += (resp.json()["data"])

with open('fb_ads_results.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(["Campaign Name", "Ad Set Name", "Ad Name", "Day", "Reach",
        "Impressions", "Post Engagement", "Clicks (All)", "CPC (All)", "CTR (All)",
        "Frequency"]
    )
    for row in data:
        writer.writerow([
            row['campaign_name'],
            row['adset_name'],
            row['ad_name'],
            row['date_start'],
            row['reach'],
            row['impressions'],
            row['inline_post_engagement'],
            row['clicks'],
            row['cpc'],
            row['ctr'],
            row['frequency']
        ])

print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(FILE_DIRECTORY + '/../google_sheet_secret.json', scope)
gsclient = gspread.authorize(credentials)

spreadsheet = gsclient.open_by_key('1MrROsQfUARGrRqmjD_kbhPokw3nB8tw-eQmC4iNu2ms')

with open('fb_ads_results.csv', 'r') as file_obj:
    content = file_obj.read()
    gsclient.import_csv(spreadsheet.id, data=content.encode(encoding='utf-8'))

print("DONE")