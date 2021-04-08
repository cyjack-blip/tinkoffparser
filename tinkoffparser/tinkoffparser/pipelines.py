# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient

class TinkoffparserPipeline:
    def __init__(self):
        # add mongodb connection
        pass

    def process_item(self, item, spider):
        print(item)
        return item
