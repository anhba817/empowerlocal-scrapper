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

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from items import UrlscrapperItem
from exporters import MyCsvItemExporter

class CsvExportPipeline:
    def open_spider(self, spider):
        customer = getattr(spider, 'customer', None)
        self.customer = customer
        sponsor_urls = getattr(spider, 'sponsor_urls', '')
        self.sponsor_urls = list(filter(len, sponsor_urls.split("\n")))
        sponsor_titles = getattr(spider, 'sponsor_titles', '')
        self.sponsor_titles = list(filter(len, sponsor_titles.split("\n")))
        out_file = getattr(spider, 'output', "%s_%s.csv" % (spider.name, customer))
        print_header = getattr(spider, 'print_header', "True")
        print_header = print_header == "True"
        self.csv_file = open(out_file, 'wb')
        self.exporter = MyCsvItemExporter(
            self.csv_file,
            fields_to_export=["source", "client", "article", "date", "title"],
            include_headers_line=print_header
        )
        self.exporter.start_exporting()
        if customer is not None and self.sponsor_urls:
            for index, sponsor_url in enumerate(self.sponsor_urls):
                item = UrlscrapperItem(
                    source=spider.name,
                    client=customer,
                    article=sponsor_url.split('/')[-2],
                    date=datetime.now().strftime("%m/%d/%Y"),
                    title=self.sponsor_titles[index]
                )
                self.exporter.export_item(item)

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.csv_file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

# class UrlscrapperPipeline:
#     def __init__(self, sponsor_urls):
#         self.sponsor_urls = sponsor_urls

#     @classmethod
#     def from_crawler(cls, crawler):
#         return cls(
#             sponsor_urls=crawler.settings.get('SPONSOR_URLS')
#         )

#     def open_spider(self, spider):
#         customer = getattr(spider, 'customer', None)
#         self.customer = customer
#         out_file = getattr(spider, 'output', None)
#         self.file = open(out_file, 'a')
#         if customer is not None and customer in self.sponsor_urls:
#             self.file.write("%s\t%s\n" % (customer, self.sponsor_urls[customer]))

#     def close_spider(self, spider):
#         self.file.close()

#     def process_item(self, item, spider):
#         adapter = ItemAdapter(item)
#         line = "%s\t%s\t%s\n" % (self.customer, adapter['article'], adapter['date'].split('T')[0])
#         self.file.write(line)
#         return item


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
            year = getattr(spider, 'year', None)
            if year is None:
                year = datetime.today().year
            month = int(month)
            year = int(year)
            last_date_of_month = calendar.monthrange(year, month)[1]
            from_date = datetime(year, month, 1)
            to_date = datetime(year, month, last_date_of_month)
            item_date = datetime.strptime(adapter['date'], "%m/%d/%Y")
            if item_date >= from_date and item_date <= to_date:
                return item
            else:
                raise DropItem(
                    f"Article is not posted in that month: {item!r}, ignore")
        else:
            return item
