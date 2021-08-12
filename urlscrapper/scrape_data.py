import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, sys
import datetime
import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

WEB_SPIDERS = {
    'WS': 'WilliamsonSource',
    'RS': 'RutherfordSource',
    'Wannado': 'Wannado',
    'WilsonCounty': 'WilsonCountySource',
    'SumnerCounty': 'SumnerCountySource',
    'RobertsonCounty': 'RobertsonCountySource',
    'CheathamCounty': 'CheathamCountySource',
    'MauryCounty': 'MauryCountySource',
    'DicksonCounty': 'DicksonCountySource',
    'DavidsonCounty': 'DavidsonCountySource'
}

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(FILE_DIRECTORY + '/../google_sheet_secret.json', scope)
client = gspread.authorize(credentials)

# client = gspread.oauth()

sh = client.open_by_key('1_W47KYXgO4XNj5QpcCkPNdJwUzl4tgy6tlwYkjIMepI')

f = open(FILE_DIRECTORY + "/web_article_results.csv", 'w')
f.write("Source,Client,Page,Date of Publish,Page Title\n")
f.close()

def parse_args(args):
    parser = argparse.ArgumentParser(description='Wrapper script to scrap data using scrapy.')
    parser.add_argument("-m", "--month", help="Month to scrap")
    parser.add_argument("-y", "--year", help="Year to scrap")
    return parser.parse_args(args)

arguments = parse_args(sys.argv[1:])

month = arguments.month
year = arguments.year
today = datetime.datetime.today()
if not month:
    month = today.month - 1 if today.month != 1 else 12
if not year:
    year = today.year if today.month != 1 else today.year - 1

file_list = []
process = CrawlerProcess(get_project_settings())
for worksheet in sh.worksheets():
    if worksheet.title not in WEB_SPIDERS:
        print("ERROR: Site is not supported: %s" % worksheet.title)
        print()
        continue
    print("Processing site %s" % WEB_SPIDERS[worksheet.title])
    if not os.path.exists(worksheet.title):
        os.mkdir(worksheet.title)
    list_of_dicts = worksheet.get_all_records()
    for row in list_of_dicts:
        if row["Customer"]:
            print("    Processing customer %s" % row['Customer'])
            out_file = "%s/%s.csv" % (worksheet.title, row['Customer'])
            file_list.append(out_file)
            process.crawl(WEB_SPIDERS[worksheet.title], customer=row['Customer'],
                urls=row['Tag URLs'], sponsor_urls=row["Sponsorship URL"],
                sponsor_titles=row['Sponsorship Page Title'], month=month,
                year=year, output=out_file, print_header="False")

print("##################################")
print("START CRAWLING DATA...")
process.start()
print("PROCESSING SCRAPED DATA...")
final_result = open(FILE_DIRECTORY+ "/web_article_results.csv", 'a+')
for myF in file_list:
    myFile = open(myF, 'r')
    final_result.write(myFile.read())
    myFile.close()
    os.remove(myF)
final_result.close()

print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
spreadsheet = client.open_by_key('1CqlVVAtsWCf5YhG3wIz5IDmfey0s6zEMJrg4768VpyY')

worksheet = spreadsheet.get_worksheet(0)
worksheet.resize(1)
with open(FILE_DIRECTORY + '/web_article_results.csv', 'r', encoding='utf-8') as file_obj:
    csv_reader = csv.reader(file_obj, delimiter=',')
    all_rows = list(csv_reader)
    worksheet.append_rows(all_rows[1:])

print("FINISHED")