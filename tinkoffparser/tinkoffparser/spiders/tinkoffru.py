import scrapy
from scrapy.http import HtmlResponse
from tinkoffparser.tinkoffparser.items import TinkoffparserItem



class TinkoffruSpider(scrapy.Spider):
    name = 'tinkoffru'
    allowed_domains = ['tinkoff.ru']
    start_urls = ['https://www.tinkoff.ru/invest/stocks/']
    base_url = 'https://www.tinkoff.ru'

    def parse(self, response:HtmlResponse):
        links = response.xpath("//table/tbody/tr/td[1]/a[contains(@data-qa-file, 'NavigateLinkPure')]/@href").extract()
        for link in links:
            yield response.follow(self.base_url+link, callback=self.stocks_parse)
        next_page = response.xpath("//a[@class='Pagination-module__item_1YVKs' and @data-qa-type='uikit/pagination.arrowRight']/@href").extract_first()
        if next_page:
            yield response.follow(self.base_url+next_page, callback=self.parse)

    def stocks_parse(self, response:HtmlResponse):
        stocks_name = response.xpath("//h1/span[@class='SecurityHeaderPure__showName_250CD']/text()").extract_first()
        ticker = response.xpath("//h1//span[@class='SecurityHeaderPure__ticker_xfPEz']/text()").extract_first()
        logo_url = response.xpath("//div[@class='SecurityHeaderPure__logo_22yS8']//span[@class='Avatar-module__image_ZCGVO']/@style").extract_first()
        sector = response.xpath("(//div[@class='SecurityHeaderPure__panelText_1h97W'])[last()]/text()").extract_first()
        description = response.xpath("//div[@data-qa-file='SecurityInfoPure' and @class='SecurityInfoPure__info_k6iQe']/div/node()").extract()
        official_website = response.xpath("//div[@class='SecurityInfoPure__link_1wZy7']/a[contains(@class, 'Link__link_2IamY')]/@href").extract_first()
        yield TinkoffparserItem(stocks_name=stocks_name, ticker=ticker, logo_url=logo_url, sector=sector, description=description, official_website=official_website)


