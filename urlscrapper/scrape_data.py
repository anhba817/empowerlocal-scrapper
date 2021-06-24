import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

WEB_SPIDERS = {
    'WS': 'WilliamsonSource',
    'RS': 'RutherfordSource',
    'Wannado': 'Wannado'
}

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

#credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret_2.json', scope)
#client = gspread.authorize(credentials)

client = gspread.oauth()

sh = client.open_by_key('1_W47KYXgO4XNj5QpcCkPNdJwUzl4tgy6tlwYkjIMepI')

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
            process.crawl(WEB_SPIDERS[worksheet.title], customer=row['Customer'],
                urls=row['Tag URLs'], sponsor_urls=row["Sponsorship URL"],
                sponsor_titles=row['Sponsorship Page Title'], month=5, output=out_file)

print("##################################")
print("START CRAWLING DATA...")
process.start()
print("FINISHED")