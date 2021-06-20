import scrapy


class WilliamsonSpider(scrapy.Spider):
    name = 'williamson'
    PAGE_MAX = 4

    def start_requests(self):
        CRAWL_URLS = self.settings.get('CRAWL_URLS')
        self.customer = getattr(self, 'customer', None)
        if not self.customer:
            print('#########################################')
            print("ERROR: No customer provided")
            print('#########################################')
        elif self.customer in CRAWL_URLS:
            start_urls = CRAWL_URLS[self.customer]
            for url in start_urls:
                yield scrapy.Request(url=url, callback=self.parse)
        else:
            print('#########################################')
            print("ERROR: Unknow customer")
            print('#########################################')

    def parse(self, response):
        title = response.xpath('//head/title/text()').get()
        post_selectors = response.css(
            '.td-ss-main-content').css('.td_module_1')
        for post in post_selectors:
            article_url = post.css('.td-module-thumb').xpath('./a/@href').get()
            article_title = post.css('.td-module-thumb').xpath('./a/@title').get() + " - Williamson Source"
            yield {
                'client': self.customer,
                'article': article_url.split('/')[-2],
                'date': post.css('.td-post-date').xpath('./time/@datetime').get(),
                'title': article_title
            }
        next_page = response.css(
            '.td-pb-padding-side').css('.current').xpath('./following-sibling::a[1]/@href').get()
        if next_page is not None and int(next_page.split('page/')[-1].split('/')[0]) < self.PAGE_MAX:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
