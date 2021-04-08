# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TinkoffparserItem(scrapy.Item):
    stocks_name = scrapy.Field()
    ticker = scrapy.Field()
    logo_url = scrapy.Field()
    sector = scrapy.Field()
    description = scrapy.Field()
    official_website = scrapy.Field()
    _id = scrapy.Field()
