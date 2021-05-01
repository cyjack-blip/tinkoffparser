import scrapy
from scrapy.http import HtmlResponse
from tinkoffparser.tinkoffparser.items import TinkoffparserItem
import re
import json
from pydispatch import dispatcher
from scrapy import signals
from copy import deepcopy


class TinkoffruSpider(scrapy.Spider):
    name = 'tinkoffru'
    allowed_domains = ['tinkoff.ru']
    start_urls = [
        'https://www.tinkoff.ru/invest/stocks/',       # 1576
        'https://www.tinkoff.ru/invest/etfs/',        # 56
        'https://www.tinkoff.ru/invest/bonds/',         # 472
        'https://www.tinkoff.ru/invest/currencies/'   # 8
        ]
    base_url = 'https://www.tinkoff.ru'
    logo_url = 'https://static.tinkoff.ru/brands/traiding/'

    info_urls = {
        'https://www.tinkoff.ru/invest/stocks/': {
            'info': 'https://www.tinkoff.ru/api/trading/stocks/get',
            'brand': 'https://www.tinkoff.ru/api/trading/symbols/brands',
            'list': 'https://www.tinkoff.ru/api/trading/stocks/list',
            'list_request': {"start":"0","end":"1584","country":"All","orderType":"Asc","sortType":"ByName"}
        },
        'https://www.tinkoff.ru/invest/etfs/': {
            'info': 'https://www.tinkoff.ru/api/trading/etfs/get',
            'brand': 'https://www.tinkoff.ru/api/trading/symbols/brands',
            'list': 'https://www.tinkoff.ru/api/trading/etfs/list',
            'list_request': {"start":"0","end":"60","country":"All","orderType":"Desc","sortType":"ByEarnings"}
        },
        'https://www.tinkoff.ru/invest/bonds/': {
            'info': 'https://www.tinkoff.ru/api/trading/bonds/get',
            'brand': 'https://www.tinkoff.ru/api/trading/symbols/brands',
            'list': 'https://www.tinkoff.ru/api/trading/bonds/list',
            'list_request': {"start":"0","end":"480","country":"All","orderType":"Desc","sortType":"ByYieldToClient"}
        },
        'https://www.tinkoff.ru/invest/currencies/': {
            'info': 'https://www.tinkoff.ru/api/trading/currency/get',
            'brand': 'https://www.tinkoff.ru/api/trading/symbols/brands',
            'list': 'https://www.tinkoff.ru/api/trading/currency/list',
            'list_request': {"pageSize":12,"currentPage":0,"start":0,"end":12,"sortType":"ByBuyBackDate","orderType":"Asc","country":"All"}
        }
    }

    def __init__(self, **kwargs):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.parced_items = []
        super().__init__(**kwargs)

    def spider_closed(self, spider):
        print(f'Spider "{spider.name}" report')
        print(self.parced_items)
        print(f'total: {len(self.parced_items)} items')

    def parse(self, response: HtmlResponse):
        # print(response.url)
        yield response.follow(
            'https://www.tinkoff.ru/api/common/v1/session?origin=web%2Cib5%2Cplatform',
            # callback=self.response_sid,
            callback=self.tickers_list_get,
            dont_filter=True,
            cb_kwargs={'url': deepcopy(response.url)}
        )

    def tickers_list_get(self, response: HtmlResponse, url):
        j_body = response.json()
        if j_body.get('resultCode') == 'OK':
            payload = j_body.get('payload')
            trackingId = j_body.get('trackingId')
            request_url = f"{self.info_urls[url]['list']}?sessionId={payload}"
            # print(request_url)
            body = self.info_urls[url]['list_request']
            yield response.follow(
                request_url,
                callback=self.tickers_info,
                method='POST',
                headers={'Content-Type': 'application/json'},
                dont_filter=True,
                body=json.dumps(body),
                cb_kwargs={'payload': payload, 'trackingId': trackingId, 'url': url}
            )

    def tickers_info(self, response, payload, trackingId, url):
        j_body = json.loads(response.text)
        if j_body['status'] == 'Ok':
            for load in j_body['payload']['values']:
                stocks_name = load['symbol']['brand']
                ticker = load['symbol']['ticker']
                time = j_body['time']
                currency = load['symbol']['currency']
                type = load['symbol']['symbolType']
                symbol = load
                item = TinkoffparserItem(stocks_name=stocks_name, ticker=ticker, logo_url='', sector='',
                                         description='', official_website='', currency=currency, type=type, time=time,
                                         symbol=symbol,
                                         brand='')
                if type != 'Currency':
                    if 'sector' in load['symbol'].keys():
                        item['sector'] = load['symbol']['sector']

                if type == 'Bond':
                    if 'fullDescription' in load['symbol'].keys():
                        item['description'] = load['symbol']['fullDescription']

                body = {'brandId': item['stocks_name']}
                request_url = self.info_urls[url]['brand'] + f'?sessionId={payload}'
                yield response.follow(
                    request_url,
                    callback=self.stocks_brand_info,
                    method='POST',
                    headers={'Content-Type': 'application/json'},
                    dont_filter=True,
                    body=json.dumps(body),
                    cb_kwargs={'item': item}
                )
        else:
            print(f"error requesting list")

    def stocks_brand_info(self, response, item):
        j_body = json.loads(response.text)
        if j_body['status'] == 'Ok':
            if j_body['payload']['brands']:
                if 'logoName' in j_body['payload']['brands'][0].keys():
                    item['logo_url'] = f"{self.logo_url}{j_body['payload']['brands'][0]['logoName'].split('.')[0]}x160.{j_body['payload']['brands'][0]['logoName'].split('.')[1]}"
                if 'brandInfo' in j_body['payload']['brands'][0].keys():
                    if not item['description']:
                        item['description'] = j_body['payload']['brands'][0]['brandInfo']
                if 'main' in j_body['payload']['brands'][0]['externalLinks'].keys():
                    item['official_website'] = j_body['payload']['brands'][0]['externalLinks']['main']
                item['brand'] = j_body['payload']['brands'][0]
            self.parced_items.append(f"{item['type']}/{item['ticker']}")
            yield item
        else:
            print(f"error brand request: {item['stocks_name']}")

    # def response_sid(self, response: HtmlResponse, url):
    #     j_body = response.json()
    #     if j_body.get('resultCode') == 'OK':
    #         payload = j_body.get('payload')
    #         trackingId = j_body.get('trackingId')
    #         request_url = f'{url}?sessionId={payload}'
    #         yield response.follow(
    #             request_url,
    #             callback=self.stocks_list_parse,
    #             cb_kwargs={'payload': payload, 'trackingId': trackingId, 'url': url}
    #         )

    # def stocks_list_parse(self, response: HtmlResponse, payload, trackingId, url):
    #     links = response.xpath("//table/tbody/tr/td[1]/a[contains(@data-qa-file, 'NavigateLinkPure')]/@href").extract()
    #     # tickers = []
    #     for link in links:
    #         # tickers.append(re.search(r'.*/(.+)/$', link).group(1))
    #         yield response.follow(
    #             self.base_url+link+f'?sessionId={payload}',
    #             callback=self.stocks_parse,
    #             cb_kwargs={'payload': payload, 'trackingId': trackingId, 'url': url}
    #         )
    #
    #     next_page = response.xpath("//a[@class='Pagination-module__item_1YVKs' and @data-qa-type='uikit/pagination.arrowRight']/@href").extract_first()
    #     if next_page:
    #         next_url = self.base_url+next_page+f'&sessionId={payload}'
    #         yield response.follow(
    #             next_url,
    #             callback=self.stocks_list_parse,
    #             cb_kwargs={'payload': payload, 'trackingId': trackingId, 'url': url}
    #         )
    #
    # def stocks_parse(self, response: HtmlResponse, payload, trackingId, url):
    #     stocks_name = response.xpath("//h1/span[@class='SecurityHeaderPure__showName_250CD']/text()").extract_first()
    #     ticker = response.xpath("//h1//span[@class='SecurityHeaderPure__ticker_xfPEz']/text()").extract_first()
    #     item = TinkoffparserItem(stocks_name=stocks_name, ticker=ticker, logo_url='', sector='',
    #                              description='', official_website='', currency='', type='', time='', symbol='', brand='')
    #     body = {'ticker': ticker}
    #     yield response.follow(
    #         self.info_urls[url]['info']+f'?sessionId={payload}',
    #         callback=self.stocks_info,
    #         method='POST',
    #         headers={'Referer': url+ticker+'/', 'Content-Type': 'application/json'},
    #         dont_filter=True,
    #         body=json.dumps(body),
    #         cb_kwargs={'payload': payload, 'trackingId': trackingId, 'url': url, 'item': item}
    #     )
    #
    # def stocks_info(self, response, payload, trackingId, url, item):
    #     j_body = json.loads(response.text)
    #     if j_body['status'] == 'Ok':
    #         item['type'] = j_body['payload']['symbol']['symbolType']
    #         item['symbol'] = j_body['payload']['symbol']
    #         item['currency'] = j_body['payload']['symbol']['currency']
    #         item['stocks_name'] = j_body['payload']['symbol']['brand']
    #         ticker = item['ticker']
    #         item['time'] = j_body['time']
    #
    #         if item['type'] != 'Currency':
    #             if 'sector' in j_body['payload']['symbol'].keys():
    #                 item['sector'] = j_body['payload']['symbol']['sector']
    #
    #         if item['type'] == 'Bond':
    #             if 'fullDescription' in j_body['payload']['symbol'].keys():
    #                 item['description'] = j_body['payload']['symbol']['fullDescription']
    #
    #         body = {'brandId': item['stocks_name']}
    #         yield response.follow(
    #             self.info_urls[url]['brand'] + f'?sessionId={payload}',
    #             callback=self.stocks_brand_info,
    #             method='POST',
    #             headers={'Referer': url + ticker + '/', 'Content-Type': 'application/json'},
    #             dont_filter=True,
    #             body=json.dumps(body),
    #             cb_kwargs={'payload': payload, 'trackingId': trackingId, 'url': url, 'item': item}
    #         )
    #     else:
    #         print(f"error info request: {item['ticker']}")

    # def stocks_parse(self, response:HtmlResponse):
    #     stocks_name = response.xpath("//h1/span[@class='SecurityHeaderPure__showName_250CD']/text()").extract_first()
    #     ticker = response.xpath("//h1//span[@class='SecurityHeaderPure__ticker_xfPEz']/text()").extract_first()
    #     logo_url = response.xpath("//div[@class='SecurityHeaderPure__logo_22yS8']//span[@class='Avatar-module__image_ZCGVO']/@style").extract_first()
    #     logo_url = 'https://'+re.search(r"static.*\.\w\w\w", logo_url).group(0)
    #     sector = response.xpath("(//div[@class='SecurityHeaderPure__panelText_1h97W'])[last()]/text()").extract_first()
    #     description = response.xpath("//div[@data-qa-file='SecurityInfoPure' and @class='SecurityInfoPure__info_k6iQe']/div/node()").extract()
    #     description = '\n'.join(description)
    #     official_website = response.xpath("//div[@class='SecurityInfoPure__link_1wZy7']/a/@href").extract_first()
    #     item = TinkoffparserItem(stocks_name=stocks_name, ticker=ticker, logo_url=logo_url, sector=sector, description=description, official_website=official_website)
    #     yield item

