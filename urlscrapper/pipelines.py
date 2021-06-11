# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from datetime import datetime
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
        if customer is not None:
            self.file = open("%s.txt" % customer, 'w')
            if customer in self.sponsor_urls:
                self.file.write("{\"article\": \"%s\", \"date\": \"None\"}\n" % self.sponsor_urls[customer])

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(ItemAdapter(item).asdict()) + "\n"
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
        from_date = getattr(spider, 'from_date', None)
        to_date = getattr(spider, 'to_date', None)
        if from_date is not None and to_date is not None:
            from_date = datetime.strptime(from_date, "%Y-%m-%d")
            to_date = datetime.strptime(to_date, "%Y-%m-%d")
            item_date = datetime.strptime(
                adapter['date'].split('T')[0], "%Y-%m-%d")
            if item_date >= from_date and item_date <= to_date:
                return item
            else:
                raise DropItem(
                    f"Article is not posted in date range: {item!r}, ignore")
        else:
            return item
