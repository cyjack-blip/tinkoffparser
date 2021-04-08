from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from tinkoffparser.tinkoffparser import settings
from tinkoffparser.tinkoffparser.spiders.tinkoffru import TinkoffruSpider


if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(TinkoffruSpider)

    process.start()


