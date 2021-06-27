# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class UrlscrapperItem(scrapy.Item):
    # define the fields for your item here like:
    source = scrapy.Field()
    client = scrapy.Field()
    article = scrapy.Field()
    date = scrapy.Field()
    title = scrapy.Field()
