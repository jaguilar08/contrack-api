from pymongo import MongoClient

from const import MONGO_CON


class MongoCon:
    def __init__(self, conf=None):
        conf = conf or MONGO_CON
        self.conf = conf
        self.cnx = MongoClient(
            conf["host"], conf["port"], username=conf["user"], password=conf["password"], authSource=conf["database"])

    def db(self):
        return self.cnx[self.conf["database"]]

    def __enter__(self):
        return self.db()

    def __exit__(self, type, value, tb):
        self.cnx.close()
