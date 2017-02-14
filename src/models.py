
from datetime import datetime
from peewee import *

db = SqliteDatabase('mydb.db', threadlocals=True)

class BaseModel(Model):
    """Base Model for all classes/tables"""
    class Meta:
        database = db

class Accounts(BaseModel):
    name = CharField(unique=True)
    ledgerBalance = FloatField()
    availableBalance = FloatField()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ledgerBalance': self.ledgerBalance,
            'availableBalance': self.availableBalance
        }

class Transactions(BaseModel):
    transactionID = CharField()
    senderID = IntegerField()
    receiverID = IntegerField()
    amount = FloatField()
    transactionType = CharField()
    transactionDate = DateTimeField(default=datetime.utcnow())

    class Meta:
        indexes = (
            # create a unique on transactionID/transactionType
            (('transactionID', 'transactionType'), True),
        )

    def to_dict(self):
        return {
            'id': self.id,
            'transactionID': self.transactionID,
            'senderID': self.senderID,
            'receiverID': self.receiverID,
            'amount': self.amount,
            'transactionType': self.transactionType,
            'transactionDate': self.transactionDate
        }

class Transfer(BaseModel):
    account = ForeignKeyField(Accounts)
    transactionID = CharField()
    amount = FloatField()
    presented = BooleanField(default=0)
    transferDate = DateTimeField(default=datetime.utcnow())
    
    def to_dict(self):
        return {
            'transferID': self.id,
            'accountName': self.account.name,
            'accountID': self.account.id,
            'transactionID': self.transactionID,
            'amount': self.amount,
            'transferDate': self.transferDate,
            'presented': self.presented
        }

    class Meta:
        indexes = (
            # create a unique on transactionID/account_id
            (('transactionID', 'account'), True),
        )

def init_db():
    db.connect()
    db.create_tables([Accounts, Transactions, Transfer], safe=True)

def close_db():
    db.close()
