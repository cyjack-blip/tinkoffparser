# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class TinkoffparserPipeline:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _client = MongoClient('localhost', 27017)
        self._mongo_base = _client['parsed']

    def process_item(self, item, spider):
        collection = self._mongo_base['stocks']
        result = collection.find_one({'ticker': item['ticker']})
        if not result:
            collection.insert_one(item)
            print(f"ADD: {item['stocks_name']} :: {item['ticker']} :: {item['type']}")
        else:
            collection.update_one({'ticker': item['ticker']},
                                  {"$unset": {'symbol': ''}})
            collection.update_one({'ticker': item['ticker']}, {"$set": {'symbol': item['symbol'], 'time': item['time']}})
            print(f"UPDATE: {item['stocks_name']} :: {item['ticker']} :: {item['type']}")
        return item
