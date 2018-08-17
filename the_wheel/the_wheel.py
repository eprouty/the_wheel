'''TheWheel: A shameful experience'''
import os
import pymongo

class TheWheel():
    def __init__(self, testDb=None):
        super().__init__()

        self.testDb = testDb

        if os.environ.get('MONGODB_URI'): # pragma: no cover
            # Production database
            self.mongoClient = pymongo.MongoClient(os.environ['MONGODB_URI'])
            self.db = self.mongoClient.the_wheel
            print("Using production database!")
        else:
            self.mongoClient = pymongo.MongoClient()
            if not testDb:  # pragma: no cover
                self.mongoClient.the_wheel
            else:
                self.db = self.mongoClient[testDb]

    def __del__(self):
        if self.testDb and self.testDb != 'the_wheel':
            self.mongoClient.drop_database(self.testDb)
