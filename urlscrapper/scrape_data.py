import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

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

credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret_2.json', scope)
client = gspread.authorize(credentials)

# client = gspread.oauth()

sh = client.open_by_key('1_W47KYXgO4XNj5QpcCkPNdJwUzl4tgy6tlwYkjIMepI')

if os.path.exists("results.csv"):
    os.remove("results.csv")
    f = open("results.csv", 'w')
    f.write("Source,Client,Page,Date of Publish,Page Title\n")
    f.close()

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
                sponsor_titles=row['Sponsorship Page Title'], month=5, output=out_file, print_header="False")

print("##################################")
print("START CRAWLING DATA...")
process.start()
print("PROCESSING SCRAPED DATA...")
final_result = open("results.csv", 'a+')
for myF in file_list:
    myFile = open(myF, 'r')
    final_result.write(myFile.read())
    myFile.close()
    os.remove(myF)
final_result.close()

print("UPLOADING SCRAPED DATA TO GOOGLE SHEET...")
spreadsheet = client.open_by_key('1CqlVVAtsWCf5YhG3wIz5IDmfey0s6zEMJrg4768VpyY')

with open('results.csv', 'r') as file_obj:
    content = file_obj.read()
    client.import_csv(spreadsheet.id, data=content.encode(encoding='utf-8'))
print("FINISHED")