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
import threading, time
from queue import Queue

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

# URLS = {
#     'williamsonsource.com': 'WilliamsonSource',
#     'rutherfordsource.com': 'RutherfordSource',
#     'wannado.com': 'Wannado',
# }

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
articles_info = worksheet.get_all_records()

mailchimp_config_client = gsclient.open_by_key('13iD3WXS9oaCNrhXjnCflHxaivXZnR4yUxu-dO7Y0F5k')
mailchimp_config = mailchimp_config_client.get_worksheet(0).get_all_records()

track_links = gsclient.open_by_key('1GSoBnWHA6MvcRxqg2zOzLPF8Gta2vdHeQSL7Jyjgv1g').get_worksheet(0).get_all_records()
# Get all mailchimp campaigns in the month

with open(FILE_DIRECTORY + '/mailchimp_campaign.csv', 'w') as campaign_file:
    campaign_writer = csv.writer(campaign_file)
    campaign_writer.writerow(['Send Time', 'Client', 'Emails Sent', 'Emails Sent Success', 'Campaign Title', 'Campaign ID',
                    'List Name', 'Subject Line', 'Total Opens', 'Unique Opens', 'Open Rate', 'Total Clicks',
                    'Unique Clicks', 'Click Rate', 'Facebook Likes'])

with open(FILE_DIRECTORY + '/mailchimp_url.csv', 'w') as url_file:
    url_writer = csv.writer(url_file)
    url_writer.writerow(['Date', 'Source', 'Client', 'Page Title', 'URL', 'Total Clicks', 'Unique Clicks'])

campaign_writer_lock = threading.Lock()
url_writer_lock = threading.Lock()

def process_queue(q):
    while not q.empty():
        try:
            mailchimp_client, campaign = q.get()
            print("Processing campaigns %s" % campaign['campaign_title'])
            send_time = campaign['send_time'][0:10]
            emails_sent = campaign['emails_sent']
            emails_sent_success = campaign['emails_sent'] - campaign["bounces"]["hard_bounces"] - campaign["bounces"]["soft_bounces"] - campaign["bounces"]["syntax_errors"]
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
            campaign_client = []
            urls_clicked = mailchimp_client.reports.get_campaign_click_details(campaign['id'], count=1000)["urls_clicked"]
            urls_info = {}
            for url in urls_clicked:
                if url['url'] in urls_info:
                    urls_info[url['url']]['total_clicks'] += url['total_clicks']
                    members = mailchimp_client.reports.get_subscribers_info(campaign['id'], url['id'], count=1000)["members"]
                    urls_info[url['url']]['members'].extend([member["email_id"] for member in members])
                else:
                    urls_info[url['url']] = {}
                    urls_info[url['url']]['total_clicks'] = url['total_clicks']
                    members = mailchimp_client.reports.get_subscribers_info(campaign['id'], url['id'], count=1000)["members"]
                    urls_info[url['url']]['members'] = [member["email_id"] for member in members]
                    urls_info[url['url']]['campaign_id'] = campaign['id']
                    urls_info[url['url']]['campaign_title'] = campaign['campaign_title']
                    urls_info[url['url']]['date'] = send_time
                    url_to_search = url['url'].split("?")[0]
                    urls_info[url['url']]['client'] = ''
                    urls_info[url['url']]['source'] = ''
                    urls_info[url['url']]['page_title'] = ''
                    track_link = next((item for item in track_links if url_to_search in item["Short tracking link"]), None)
                    if track_link:
                        campaign_client.append(track_link['Campaign name'])
                    elif len(url_to_search.split("/")) >=4:
                        article = next((item for item in articles_info if url_to_search == URLS[item['Source']] + item["Page"] + "/"), None)
                        if article:
                            urls_info[url['url']]['client'] = article['Client']
                            urls_info[url['url']]['source'] = article['Source']
                            urls_info[url['url']]['page_title'] = article['Page Title']
                            campaign_client.append(article['Client'])

            while campaign_writer_lock.locked():
                time.sleep(0.05)
                continue
            campaign_writer_lock.acquire()
            f = open(FILE_DIRECTORY + '/mailchimp_campaign.csv', 'a+')
            writer = csv.writer(f)
            writer.writerow([
                send_time,
                ", ".join(set(campaign_client)),
                emails_sent,
                emails_sent_success,
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
            f.close()
            campaign_writer_lock.release()

            while url_writer_lock.locked():
                time.sleep(0.05)
                continue
            url_writer_lock.acquire()
            f = open(FILE_DIRECTORY + '/mailchimp_url.csv', 'a+')
            url_writer = csv.writer(f)
            for url_info in urls_info:
                url_writer.writerow([
                    urls_info[url_info]['date'],
                    urls_info[url_info]['source'],
                    urls_info[url_info]['client'],
                    urls_info[url_info]['page_title'],
                    url_info,
                    urls_info[url_info]['total_clicks'],
                    len(list(set(urls_info[url_info]['members']))),
                ])
            f.close()
            url_writer_lock.release()
            q.task_done()
        except Exception as e:
            print(e)
            print("    Error happen when processing campaign %s" % campaign['campaign_title'])
            q.task_done()

for server in mailchimp_config:
    try:
        print("Processing server %s" % server['Server'])
        mailchimp_client = MailchimpMarketing.Client()
        mailchimp_client.set_config({
            "api_key": server['API KEY'],
            "server": server['Server']
        })
        print("Getting campaigns from mailchimp...")
        campaigns = mailchimp_client.reports.get_all_campaign_reports( count=1000,
                                                     since_send_time=startDate.isoformat(),
                                                     before_send_time=stopDate.isoformat()
                                                    )["reports"]
        print("Found %s campaigns" % len(campaigns))

        # threads = []
        jobs = Queue()

        for campaign in campaigns:
            jobs.put((mailchimp_client, campaign))

        for _ in range(5):
            t = threading.Thread(target=process_queue, args=(jobs,))
            # threads.append(t)
            t.start()
        # [thread.join() for thread in threads]
        jobs.join()

    except ApiClientError as error:
        print("Error: {}".format(error.text))


print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
# Campaign data
spreadsheet = gsclient.open_by_key('1X8eD6Djeqcif5OvAlydYLqD7wZmIjB_nweu1n4Paodw')
worksheet = spreadsheet.get_worksheet(0)
worksheet.resize(1)
with open(FILE_DIRECTORY + '/mailchimp_campaign.csv', 'r', encoding='utf-8') as file_obj:
    csv_reader = csv.reader(file_obj, delimiter=',')
    all_rows = list(csv_reader)
    worksheet.append_rows(all_rows[1:])

# URL data
spreadsheet2 = gsclient.open_by_key('1i0oYDHq50WlRinIj6EolVJPOk9NDSWIsB7VQqpHKRE0')
worksheet2 = spreadsheet2.get_worksheet(0)
# worksheet2.resize(1)
with open(FILE_DIRECTORY + '/mailchimp_url.csv', 'r', encoding='utf-8') as file_obj:
    csv_reader = csv.reader(file_obj, delimiter=',')
    all_rows = list(csv_reader)
    worksheet2.append_rows(all_rows[1:])
print("SCRAPPING DONE")
