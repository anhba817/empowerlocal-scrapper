import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone
import argparse
import os, sys, calendar, csv

URLS = {
    'WilliamsonSource': 'https://williamsonsource.com/',
    'RutherfordSource': 'https://rutherfordsource.com/',
    'Wannado': 'https://wannado.com/',
}

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

startDate = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
last_day_in_month = calendar.monthrange(year, month)[1]
stopDate = datetime(year, month, last_day_in_month, 23, 59, 59, tzinfo=timezone.utc)

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name('urlscrapper/client_secret_2.json', scope)
gsclient = gspread.authorize(credentials)

# client = gspread.oauth()

sh = gsclient.open_by_key('1CqlVVAtsWCf5YhG3wIz5IDmfey0s6zEMJrg4768VpyY')
worksheet = sh.get_worksheet(0)
list_of_dicts = worksheet.get_all_records()

# Get all mailchimp campaigns in the month
ws_rs_campaigns = []
try:
    ws_rs_client = MailchimpMarketing.Client()
    ws_rs_client.set_config({
      "api_key": "f08427aa56aca85c4ebfbcee4e28b3ea-us5",
      "server": "us5"
    })

    response = ws_rs_client.campaigns.list(count=1000,
      since_send_time=startDate.isoformat(),
      before_send_time=stopDate.isoformat()
    )
    ws_rs_campaigns = response['campaigns']
    print("GETTING WS/RS CAMPAIGNS INFO FROM MAILCHIMP...")
    for campaign in ws_rs_campaigns:
        campaign['content'] = ws_rs_client.campaigns.get_content(campaign['id'], fields=['plain_text'])
except ApiClientError as error:
    print("Error: {}".format(error.text))

wannado_campaigns = []
try:
    wannado_client = MailchimpMarketing.Client()
    wannado_client.set_config({
      "api_key": "bbdf9344ecceabc730a8227a66544942-us3",
      "server": "us3"
    })

    response = wannado_client.campaigns.list(count=1000,
      since_send_time=startDate.isoformat(),
      before_send_time=stopDate.isoformat()
    )
    wannado_campaigns = response['campaigns']
    print("GETTING WANNDDO CAMPAIGNS INFO FROM MAILCHIMP...")
    for campaign in wannado_campaigns:
        campaign['content'] = wannado_client.campaigns.get_content(campaign['id'], fields=['plain_text'])
except ApiClientError as error:
    print("Error: {}".format(error.text))


not_found = []
with open('mailchimp_results.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(["Source", "Client", "Page", "Date of Publish", "Page Title", "Campaigns ID", "Campaigns Title"])

    for article in list_of_dicts:
        print("Processing article: %s" % article['Page Title'])
        url_to_search = URLS[article['Source']] + article['Page'] + "/"
        # Go through all campaigns and search
        campaign_id = ''
        campaign_title = ''
        if article['Source'] == "Wannado":
            for campaign in wannado_campaigns:
                if url_to_search in campaign['content']['plain_text']:
                    campaign_id = campaign['id']
                    campaign_title = campaign['settings']['title']
        else:
            for campaign in ws_rs_campaigns:
                if url_to_search in campaign['content']['plain_text']:
                    campaign_id = campaign['id']
                    campaign_title = campaign['settings']['title']

        if not campaign_id:
            not_found.append(url_to_search)
        writer.writerow([
            article['Source'],
            article['Client'],
            article['Page'],
            article['Date of Publish'],
            article['Page Title'],
            campaign_id,
            campaign_title
        ])
print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
spreadsheet = gsclient.open_by_key('19On7_SSqJPhlmY3ZHjYmZ0Jvc0Gh_NoavWq9uZeUTio')

with open('mailchimp_results.csv', 'r') as file_obj:
    content = file_obj.read()
    gsclient.import_csv(spreadsheet.id, data=content.encode(encoding='utf-8'))

print("SCRAPPING DONE")
print("ARTICLES NOT INCLUDES In ANY NEWSLETTER:")
for post in not_found:
    print(post)

print("######### DONE ###########")