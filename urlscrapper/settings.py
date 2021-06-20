# Scrapy settings for urlscrapper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import pathlib
BOT_NAME = 'urlscrapper'

SPIDER_MODULES = ['urlscrapper.spiders']
NEWSPIDER_MODULE = 'urlscrapper.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'urlscrapper (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'urlscrapper.middlewares.UrlscrapperSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'urlscrapper.middlewares.UrlscrapperDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'urlscrapper.pipelines.DuplicatesPipeline': 100,
    'urlscrapper.pipelines.FilterDatePipeline': 200,
    'urlscrapper.pipelines.CsvExportPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

CRAWL_URLS = {
    'A Moment Peace': [
        'https://williamsonsource.com/tag/a-moments-peace/',
        'https://williamsonsource.com/tag/a-moments-peace-salon-and-day-spa/',
        'https://williamsonsource.com/tag/style/'
    ],
    'Franklin Athletic Club': [
        'https://williamsonsource.com/tag/franklin-athletic-club/',
        'https://williamsonsource.com/tag/health-fitness/'
    ],
    'Bone and Joint Institute of TN': [
        'https://williamsonsource.com/tag/bone-and-joint-institute/',
        'https://williamsonsource.com/tag/bone-and-joint-institute-of-tennessee/'
    ],
    'Brentwood Place': [
        'https://williamsonsource.com/tag/brentwood-place/',
        'https://williamsonsource.com/tag/brentwood/'
    ],
    'Caregivers by Wholecare': ['https://williamsonsource.com/tag/caregivers-by-wholecare/'],
    'Columbia Crawlspace': ['https://williamsonsource.com/tag/columbia-crawlspace/'],
    'Coyne Oral Surgery & Dental Implant Center': ['https://williamsonsource.com/tag/coyne-oral-surgery-dental-implant-center/'],
    'Dr. Wes Orthodontics': ['https://williamsonsource.com/tag/dr-wes-orthodontics/'],
    'Empire Managed Solutions': ['https://williamsonsource.com/tag/empire-managed-solutions/'],
    'EnviroBinz Trash Bin Cleaning Services': [
        'https://williamsonsource.com/tag/envirobinz/',
        'https://williamsonsource.com/tag/envirobinz-trash-bin-cleaning-services/'
    ],
    "French's Cabinet Gallery": ['https://williamsonsource.com/tag/frenchs-cabinet-gallery/'],
    'Harpeth Valley Dermatology': ['https://williamsonsource.com/tag/jjs-wine-bar/'],
    'Learning Lab - Brentwood & Nashville': ['https://williamsonsource.com/tag/learning-lab/'],
    "McCall's Carpet One": ['https://williamsonsource.com/tag/mccalls-carpet-one/'],
    'Papa C Pies': ['https://williamsonsource.com/tag/papa-c-pies/'],
    'Peek Pools & Spas': [
        'https://williamsonsource.com/tag/peek-pools/',
        'https://williamsonsource.com/tag/peek-pools-and-spas/',
        'https://williamsonsource.com/tag/kids-and-family/'
    ],
    'Play It Again Sports': ['https://williamsonsource.com/tag/play-it-again-sports/'],
    'Pretty in Pink Boutique': [
        'https://williamsonsource.com/tag/pretty-in-pink/',
        'https://williamsonsource.com/tag/pretty-in-pink-boutique/'
    ],
    'Soltea': ['https://williamsonsource.com/tag/soltea/'],
    'Susan Gregory': [
        'https://williamsonsource.com/tag/susan-gregory/',
        'https://williamsonsource.com/tag/real-estate/'

    ],
    'Three Dog Bakery': ['https://williamsonsource.com/tag/three-dog-bakery/'],
    'Warren Bradley Partners': [
        'https://williamsonsource.com/tag/warren-bradley-partners/',
        'https://williamsonsource.com/tag/warren-bradley/',
        'https://williamsonsource.com/tag/relocating-to-williamson-county/'
    ],
    'Westhaven Golf': ['https://williamsonsource.com/tag/westhaven-golf-club/'],
    'Williamson Medical Center': [
        'https://williamsonsource.com/tag/williamson-medical-center/',
        'https://williamsonsource.com/tag/wmc/',
    ],
    'TN Farmaceuticals': ['https://williamsonsource.com/tag/tennessee-farmaceuticals/']
}

SPONSOR_URLS = {
    'A Moment Peace': {
        'url': 'https://williamsonsource.com/style/',
        'title': "Style - Williamson Source"
    },
    'Franklin Athletic Club': {
        'url': 'https://williamsonsource.com/health-fitness/',
        'title': "Health & Fitness - Williamson Source"
    },
    'Brentwood Place': {
        'url': 'https://williamsonsource.com/brentwood/',
        'title': "Brentwood TN"
    },
    'Delivery.com': {
        'url': 'https://williamsonsource.com/eat-and-drink/',
        'title': "Eat & Drink - Williamson Source"
        },
    'Peek Pools & Spas': {
        'url': 'https://williamsonsource.com/kids-and-family/',
        'title': "Kids & Family - Williamson Source"
    },
    'Warren Bradley Partners': {
        'url': 'https://williamsonsource.com/relocating-to-williamson-county/',
        'title': "Relocating to Williamson County - Williamson Source"
    },
}

# FEEDS = {
#     pathlib.Path('result.csv'): {
#         'format': 'csv',
#         'fields': None,
#     },
# }