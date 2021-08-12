import calendar, time
import json, csv
from datetime import datetime
from dateutil.parser import parse
import re, os

import facebook

import requests, threading
from queue import Queue
from bs4 import BeautifulSoup

import gspread
from oauth2client.service_account import ServiceAccountCredentials

headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36'}

today = datetime.today()
month = today.month - 1 if today.month != 1 else 12
year = today.year if today.month != 1 else today.year - 1

last_day_in_month = calendar.monthrange(year, month)[1]

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
f = open(FILE_DIRECTORY + '/facebook.json', 'r')
auth_data = json.load(f)
f.close()

graph = facebook.GraphAPI(access_token=auth_data['page']['token'], version=auth_data['sdk_version'])

###### Get customer info from Google Sheet #######
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(FILE_DIRECTORY + '/../google_sheet_secret.json', scope)
client = gspread.authorize(credentials)
sh = client.open_by_key('1lNZksC-_80JWt1MYvFmbYNbyUC2zmhPrTphHMDFpKzM')
facebook_page_info = sh.get_worksheet(0).get_all_records()

sh2 = client.open_by_key('1_W47KYXgO4XNj5QpcCkPNdJwUzl4tgy6tlwYkjIMepI')
file_list = []

global_lock = threading.Lock()

def process_queue(q):
    while not q.empty():
        try:
            page_info, post, index = q.get()
            if 'message' in post:
                print("    Processing post %s: %s" % (index, post['message']))
            else:
                print("    Post %s does not include a message, skip!" % post)
                q.task_done()
                continue
            created_time = parse(post["created_time"]).strftime('%m/%d/%Y %I:%M:%S %p')
            data = graph.get_connections(
                id=post["id"],
                connection_name="insights",
                metric="post_impressions_unique,post_impressions,post_engaged_users,post_clicks",
                period="lifetime",
                show_description_from_api_doc=True,
            )["data"]
            total_reach = 0
            total_impressions = 0
            engaged_users = 0
            clicks = 0
            for info in data:
                if info["name"] == "post_clicks":
                    clicks = info["values"][0]["value"]
                elif info["name"] == "post_impressions_unique":
                    total_reach = info["values"][0]["value"]
                elif info["name"] == "post_impressions":
                    total_impressions = info["values"][0]["value"]
                elif info["name"] == "post_engaged_users":
                    engaged_users = info["values"][0]["value"]
                else:
                    print("########## ERROR: Unknown metric in response ###############")
            post_message = ''
            customer = ''
            post_message = re.sub('[\n\t]', '', post['message'])
            search = re.search("(?P<url>https?://[^\s]+)", post_message)
            if search:
                url = search.group("url")
                i = requests.get(url, allow_redirects=False)
                if 'location' in i.headers:
                    urlpath = i.headers['location']
                else:
                    urlpath = url
                if page_info["URL"] in urlpath:
                    req = requests.get(urlpath, headers=headers)
                    sponsor_post = next((item for item in list_of_dicts if item["Sponsorship URL"] == req.url), None)
                    if sponsor_post:
                        customer = sponsor_post["Customer"]
                    else: # Find the customer name by tags
                        soup = BeautifulSoup(req.text, 'html.parser')
                        div_tag = soup.find("div", class_=page_info["Tag class name"])
                        if div_tag and div_tag.find('ul'):
                            a_tags = div_tag.find('ul').find_all('a')
                            tags = [a['href'] for a in a_tags]
                            for tag in tags:
                                info = next((item for item in list_of_dicts if tag in item["Tag URLs"]), None)
                                if info:
                                    customer = info["Customer"]
                                    break
        except:
            print("    Error happen when processing post %s" % post['message'])
            q.task_done()
            continue

        while global_lock.locked():
            time.sleep(0.05)
            continue
        global_lock.acquire()
        f = open(FILE_DIRECTORY + '/fb_post_results.csv', 'a+')
        writer = csv.writer(f)
        writer.writerow([page_info["Name"], customer, post_message, created_time, total_reach, total_impressions,engaged_users, clicks])
        f.close()
        global_lock.release()
        q.task_done()

myFile = open(FILE_DIRECTORY + '/fb_post_results.csv', 'w')
csvWriter = csv.writer(myFile)
csvWriter.writerow(["Source", "Customer", "Post Message", "Posted", "Total Reach", "Total Impressions","Engaged Users", "Clicks"])
myFile.close()

for worksheet in sh2.worksheets():
    facebook_page = [p for p in facebook_page_info if p['Sheet'] == worksheet.title]
    if not facebook_page:
        print("ERROR: Site is not supported: %s" % worksheet.title)
        print()
        continue
    print("Processing site %s" % facebook_page[0]['Name'])
    # if not os.path.exists(worksheet.title):
    #     os.mkdir(worksheet.title)
    list_of_dicts = worksheet.get_all_records()
    # All posts in last month
    all_posts_in_month = graph.get_all_connections(
        id=facebook_page[0]['Facebook Page ID'], connection_name="posts",
        since=datetime(year, month, 1, 0, 0, 0),
        until=datetime(year, month, last_day_in_month, 23, 59, 59),
    )
    # threads = []
    jobs = Queue()
    for index, post in enumerate(all_posts_in_month):
        jobs.put((facebook_page[0], post, index,))

    for _ in range(8):
        t = threading.Thread(target=process_queue, args=(jobs,))
        # threads.append(t)
        t.start()
    # [thread.join() for thread in threads]
    jobs.join()

print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
spreadsheet = client.open_by_key('1uOFJHbns2ftrMuBm0l4BFHRHdKwYlETK1Jw_IfNhxAs')

worksheet = spreadsheet.get_worksheet(0)
worksheet.resize(1)
with open(FILE_DIRECTORY + '/fb_post_results.csv', 'r', encoding='utf-8') as file_obj:
    csv_reader = csv.reader(file_obj, delimiter=',')
    all_rows = list(csv_reader)
    worksheet.append_rows(all_rows[1:])

print("######### DONE ###########")
