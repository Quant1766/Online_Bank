
import base64
import uuid
from functools import wraps

import bcrypt
from flask import Flask, Response, request

from global_settings import *
from models import *


def basic_auth_check(username, password):
    """Basic authentication check.

    1. Find account from the database with the provided username.
    2. If account is found use the authenticate method to check that the provided plain text password
    match the stored hashed password.

    Not in use now!
    """
    try:
        account = Accounts.get(Accounts.name == username)
        return account.authenticate(password)    
    except Exception as error:
        return False

def auth_check(username, password):
    return username == BASIC_AUTH_UN and password == BASIC_AUTH_PW

def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not auth_check(auth.username, auth.password):
            return Response(
                'Not authorized to view this route',
                401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )

        return f(*args, **kwargs)
    return decorated

def hash_password(plain_text):
    """Hash plain text passwords"""
    # hash password with bcrypt and random salt
    hashed = bcrypt.hashpw(str.encode(plain_text), bcrypt.gensalt())
    # convert bytes to base64 encoded string and store this to db
    return base64.b64encode(hashed).decode("utf-8")

def transaction_check(req, sender, receiver):
    """Transaction validity check."""
    # if transaction type is 'presentment' check that previous authorization transaction can be found
    if req['transactionType'] == TRANSACTION_TYPES[1]:
        try:
            auth_transaction = Transactions.get(Transactions.transactionID == req['transactionID'])
            if auth_transaction.transactionID != req['transactionID']:
                return False
        except Exception:
            return False
    # check that the sender and receiver and the sent amount are valid.
    # Amount must be more than 1.0 and less than the available balance of the account
    if sender.id == req['senderID'] and\
    receiver.id == req['receiverID'] and\
    float(req['amount']) >= MINIMUM_TRANSFER and\
    req['transactionType'] in TRANSACTION_TYPES and\
    sender.availableBalance >= float(req['amount']):
        return True
    return False

def insert_transfer(req, sender, receiver):
    """Insert non-presented entries to Transfer table, including bank fee entry.
        presented value is not needed because the default value is set to 0.
        Transfer model (account_id + transactionID = unique constraint):
            account_id,
            transactionID,
            amount,
            presented
    """
    fee_amount = round(BANK_FEE_PERCENT * req['amount'] / 100.00, 2)
    data = [
        {
            'account': sender.id,
            'transactionID': req['transactionID'],
            'amount': round(-req['amount'], 2)
        },
        {
            'account': receiver.id,
            'transactionID': req['transactionID'],
            'amount': round(req['amount']-fee_amount, 2)
        },
        {
            'account': BANK_ID,
            'transactionID': req['transactionID'],
            'amount': fee_amount
        }
    ]
    with db.atomic():
        Transfer.insert_many(data).execute()
