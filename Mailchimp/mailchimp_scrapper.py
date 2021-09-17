import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime, timezone
import argparse
import os
import sys
import calendar
import csv
import json

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

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
stopDate = datetime(year, month, last_day_in_month,
                    23, 59, 59, tzinfo=timezone.utc)

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    FILE_DIRECTORY + '/../credentials/google_sheet_secret.json', scope)
gsclient = gspread.authorize(credentials)

# client = gspread.oauth()

sh = gsclient.open_by_key('1CqlVVAtsWCf5YhG3wIz5IDmfey0s6zEMJrg4768VpyY')
worksheet = sh.get_worksheet(0)
list_of_dicts = worksheet.get_all_records()

# Get all mailchimp campaigns in the month
f = open(FILE_DIRECTORY + '/../credentials/mailchimp_secret.json', 'r')
mailchimp_auth = json.load(f)
f.close()
ws_rs_campaigns_reports = []

try:
    ws_rs_client = MailchimpMarketing.Client()
    ws_rs_client.set_config({
        "api_key": mailchimp_auth['ws_rs']['api_key'],
        "server": mailchimp_auth['ws_rs']['server']
    })

    response = ws_rs_client.reports.get_all_campaign_reports(count=1000,
                                                             since_send_time=startDate.isoformat(),
                                                             before_send_time=stopDate.isoformat()
                                                             )
    ws_rs_campaigns_reports = response['reports']
    print("GETTING WS/RS CAMPAIGNS CONTENT FROM MAILCHIMP...")
    for campaign in ws_rs_campaigns_reports:
        campaign['content'] = ws_rs_client.campaigns.get_content(
            campaign['id'], fields=['html'])
except ApiClientError as error:
    print("Error: {}".format(error.text))

wannado_campaign_reports = []
# try:
#     wannado_client = MailchimpMarketing.Client()
#     wannado_client.set_config({
#       "api_key": mailchimp_auth['wannado']['api_key'],
#       "server": mailchimp_auth['wannado']['server']
#     })

#     response = wannado_client.campaigns.list(count=1000,
#       since_send_time=startDate.isoformat(),
#       before_send_time=stopDate.isoformat()
#     )
#     wannado_campaigns = response['campaigns']
#     print("GETTING WANNDDO CAMPAIGNS INFO FROM MAILCHIMP...")
#     for campaign in wannado_campaigns:
#         campaign['content'] = wannado_client.campaigns.get_content(campaign['id'], fields=['html'])
# except ApiClientError as error:
#     print("Error: {}".format(error.text))

not_found = []
with open(FILE_DIRECTORY + '/mailchimp_results.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(["Source", "Client", "Page", "Date of Publish", "Page Title", 'Send Time', 'Emails Sent', 'Campaign Title', 'Campaign ID',
                    'List Name', 'Subject Line', 'Total Opens', 'Unique Opens', 'Open Rate', 'Total Clicks', 'Unique Clicks', 'Click Rate', 'Facebook Likes'])

    for article in list_of_dicts:
        print("Processing article: %s" % article['Page Title'])
        url_to_search = URLS[article['Source']] + article['Page'] + "/"
        # Go through all campaigns and search
        send_time = ''
        emails_sent = ''
        campaign_id = ''
        campaign_title = ''
        list_name = ''
        subject_line = ''
        opens_total = ''
        unique_opens = ''
        open_rate = ''
        clicks_total = ''
        unique_clicks = ''
        click_rate = ''
        facebook_likes = ''
        report_data = []
        if article['Source'] == "Wannado":
            report_data = wannado_campaign_reports
        else:
            report_data = ws_rs_campaigns_reports
        for campaign in report_data:
            if url_to_search in campaign['content']['html']:
                send_time = campaign['send_time'][0:10]
                emails_sent = campaign['emails_sent']
                campaign_id = campaign['id']
                campaign_title = campaign['campaign_title']
                list_name = campaign['list_name']
                subject_line = campaign['subject_line']
                opens_total = campaign['opens']['opens_total']
                unique_opens = campaign['opens']['unique_opens']
                open_rate = campaign['opens']['open_rate']
                clicks_total = campaign['clicks']['clicks_total']
                unique_clicks = campaign['clicks']['unique_clicks']
                click_rate = campaign['clicks']['click_rate']
                facebook_likes = campaign['facebook_likes']['facebook_likes']
                break

        if not campaign_id:
            not_found.append(url_to_search)
        writer.writerow([
            article['Source'],
            article['Client'],
            article['Page'],
            article['Date of Publish'],
            article['Page Title'],
            send_time,
            emails_sent,
            campaign_title,
            campaign_id,
            list_name,
            subject_line,
            opens_total,
            unique_opens,
            open_rate,
            clicks_total,
            unique_clicks,
            click_rate,
            facebook_likes
        ])

print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
spreadsheet = gsclient.open_by_key('19On7_SSqJPhlmY3ZHjYmZ0Jvc0Gh_NoavWq9uZeUTio')

worksheet = spreadsheet.get_worksheet(0)
worksheet.resize(1)
with open(FILE_DIRECTORY + '/mailchimp_results.csv', 'r', encoding='utf-8') as file_obj:
    csv_reader = csv.reader(file_obj, delimiter=',')
    all_rows = list(csv_reader)
    worksheet.append_rows(all_rows[1:])

print("SCRAPPING DONE")
print("ARTICLES NOT INCLUDED IN ANY NEWSLETTER:")
for post in not_found:
    print(post)

print("######### DONE ###########")
