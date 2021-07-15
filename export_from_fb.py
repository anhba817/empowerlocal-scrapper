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

WEB_SPIDERS = {
    'WS': { 'name': 'WilliamsonSource', 'url': 'https://williamsonsource.com/', 'page_id': '230344097046602', 'class_name': 'td-post-source-tags'}
}

headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36'}

today = datetime.today()
month = today.month - 1 if today.month != 1 else 12
year = today.year if today.month != 1 else today.year - 1

last_day_in_month = calendar.monthrange(year, month)[1]

auth_data = json.load(open('facebook.json', 'r'))
graph = facebook.GraphAPI(access_token=auth_data['page']['token'], version=auth_data['sdk_version'])

###### Get customer info from Google Sheet #######
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name('urlscrapper/client_secret_2.json', scope)
client = gspread.authorize(credentials)
sh = client.open_by_key('1_W47KYXgO4XNj5QpcCkPNdJwUzl4tgy6tlwYkjIMepI')
file_list = []

global_lock = threading.Lock()

def process_queue(q):
    while not q.empty():
        page_info, post, index = q.get()
        print("    Processing post %s: %s" % (index, post['message']))
        created_time = parse(post["created_time"]).strftime('%m/%d/%Y %I:%M:%S %p')
        # --------------------------------- CLICKS ---------------------------------
        # The number of clicks anywhere in your post on News Feed from the user that matched the audience targeting on it.
        # (Total Count)
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
        if "message" in post:
            post_message = re.sub('[\n\t]', '', post['message'])
            search = re.search("(?P<url>https?://[^\s]+)", post_message)
            if search:
                url = search.group("url")
                i = requests.get(url, allow_redirects=False)
                if 'location' in i.headers:
                    urlpath = i.headers['location']
                else:
                    urlpath = url
                if page_info["url"] in urlpath:
                    req = requests.get(urlpath, headers=headers)
                    sponsor_post = next((item for item in list_of_dicts if item["Sponsorship URL"] == req.url), None)
                    if sponsor_post:
                        customer = sponsor_post["Customer"]
                    else: # Find the customer name by tags
                        soup = BeautifulSoup(req.text, 'html.parser')
                        div_tag = soup.find("div", class_=page_info["class_name"])
                        if div_tag and div_tag.find('ul'):
                            a_tags = div_tag.find('ul').find_all('a')
                            tags = [a['href'] for a in a_tags]
                            for tag in tags:
                                info = next((item for item in list_of_dicts if tag in item["Tag URLs"]), None)
                                if info:
                                    customer = info["Customer"]
                                    break
        while global_lock.locked():
            time.sleep(0.01)
            continue
        global_lock.acquire()
        f = open('results.csv', 'a+')
        writer = csv.writer(f)
        writer.writerow([page_info["name"], customer, post_message, created_time, total_reach, total_impressions,engaged_users, clicks])
        f.close()

        global_lock.release()
        time.sleep(0.5)
        q.task_done()

myFile = open('results.csv', 'w')
csvWriter = csv.writer(myFile)
csvWriter.writerow(["Source", "Customer", "Post Message", "Posted", "Total Reach", "Total Impressions","Engaged Users", "Clicks"])
myFile.close()

for worksheet in sh.worksheets():
    if worksheet.title not in WEB_SPIDERS:
        print("ERROR: Site is not supported: %s" % worksheet.title)
        print()
        continue
    print("Processing site %s" % WEB_SPIDERS[worksheet.title]['name'])
    # if not os.path.exists(worksheet.title):
    #     os.mkdir(worksheet.title)
    list_of_dicts = worksheet.get_all_records()
    # All posts in last month
    all_posts_in_month = graph.get_all_connections(
        id=WEB_SPIDERS[worksheet.title]['page_id'], connection_name="posts",
        since=datetime(year, month, 1, 0, 0, 0),
        until=datetime(year, month, last_day_in_month, 23, 59, 59),
    )
    # threads = []
    jobs = Queue()
    for index, post in enumerate(all_posts_in_month):
        jobs.put((WEB_SPIDERS[worksheet.title], post, index,))

    for _ in range(8):
        t = threading.Thread(target=process_queue, args=(jobs,))
        # threads.append(t)
        t.start()
    # [thread.join() for thread in threads]
    jobs.join()

print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
spreadsheet = client.open_by_key('1uOFJHbns2ftrMuBm0l4BFHRHdKwYlETK1Jw_IfNhxAs')

with open('results.csv', 'r') as file_obj:
    content = file_obj.read()
    client.import_csv(spreadsheet.id, data=content.encode(encoding='utf-8'))

print("######### DONE ###########")