from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())

# 'williamson' is the name of one of the spiders of the project.
process.crawl('williamson', customer='A Moment Peace', month=5)
process.start() # the script will block here until the crawling is finished