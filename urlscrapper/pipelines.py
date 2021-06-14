# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from datetime import datetime
import calendar
import json


class UrlscrapperPipeline:
    def __init__(self, sponsor_urls):
        self.sponsor_urls = sponsor_urls

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            sponsor_urls=crawler.settings.get('SPONSOR_URLS')
        )

    def open_spider(self, spider):
        customer = getattr(spider, 'customer', None)
        self.customer = customer
        out_file = getattr(spider, 'output', None)
        self.file = open(out_file, 'a')
        if customer is not None and customer in self.sponsor_urls:
            self.file.write("%s\t%s\n" % (customer, self.sponsor_urls[customer]))

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        line = "%s\t%s\t%s\n" % (self.customer, adapter['article'], adapter['date'].split('T')[0])
        self.file.write(line)
        return item


class DuplicatesPipeline:

    def __init__(self):
        self.articles_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter['article'] in self.articles_seen:
            raise DropItem(f"Duplicate item found: {item!r}")
        else:
            self.articles_seen.add(adapter['article'])
            return item


class FilterDatePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        month = getattr(spider, 'month', None)
        if month is not None:
            month = int(month)
            year = datetime.today().year
            last_date_of_month = calendar.monthrange(year, month)[1]
            from_date = datetime(year, month, 1)
            to_date = datetime(year, month, last_date_of_month)
            item_date = datetime.strptime(
                adapter['date'].split('T')[0], "%Y-%m-%d")
            if item_date >= from_date and item_date <= to_date:
                return item
            else:
                raise DropItem(
                    f"Article is not posted in that month: {item!r}, ignore")
        else:
            return item
