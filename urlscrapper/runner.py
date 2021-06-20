from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os

CUSTOMER = [
    'A Moment Peace',
    'Franklin Athletic Club',
    'Bone and Joint Institute of TN',
    'Brentwood Place',
    'Caregivers by Wholecare',
    'Columbia Crawlspace',
    'Coyne Oral Surgery & Dental Implant Center',
    'Dr. Wes Orthodontics',
    'Empire Managed Solutions',
    'EnviroBinz Trash Bin Cleaning Services',
    "French's Cabinet Gallery",
    'Harpeth Valley Dermatology',
    'Learning Lab - Brentwood & Nashville',
    "McCall's Carpet One",
    'Papa C Pies',
    'Peek Pools & Spas',
    'Play It Again Sports',
    'Pretty in Pink Boutique',
    'Soltea',
    'Susan Gregory',
    'Three Dog Bakery',
    'Warren Bradley Partners',
    'Westhaven Golf',
    'Williamson Medical Center',
    'TN Farmaceuticals'
]

if os.path.exists("result.csv"):
    os.remove("result.csv")
    f = open("result.csv", 'w')
    f.write("Client,Page,Date of Publish,Page Title\n")
    f.close()

process = CrawlerProcess(get_project_settings())

# 'williamson' is the name of one of the spiders of the project.
file_list = []
for index, customer in enumerate(CUSTOMER):
    out_file = "result_%s.csv" % index
    file_list.append(out_file)
    process.crawl('williamson', customer=customer, month=5, output=out_file, print_header="False")
process.start() # the script will block here until the crawling is finished

final_result = open("result.csv", 'a+')
for myF in file_list:
    myFile = open(myF, 'r')
    final_result.write(myFile.read())
    myFile.close()
    os.remove(myF)

final_result.close()