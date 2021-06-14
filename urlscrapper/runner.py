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
    f.write("Customer\tURL\tDate\n")
    f.close()

process = CrawlerProcess(get_project_settings())

# 'williamson' is the name of one of the spiders of the project.
for customer in CUSTOMER:
    process.crawl('williamson', customer=customer, month=6, output="result.csv")
process.start() # the script will block here until the crawling is finished