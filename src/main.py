
"""main app"""

import base64
import uuid
from functools import wraps

import bcrypt
from flask import Flask, Response, jsonify, request

from helpers import *
from global_settings import *
from models import *

app = Flask(__name__)

# helper and utility functions
@app.before_request
def before_request():
    # this function create tables at the database if they don't exist
    init_db()

@app.after_request
def after_request(response):
    close_db()
    return response

# root
@app.route('/')
@basic_auth_required
def root():
    """Root needs basic authentication for POC purpose."""
    return "Go to: /api/accounts"

# API routes
@app.route('/api/accounts/<int:account_id>')
@app.route('/api/accounts')
def api_get_accounts(account_id=None):
    data = None
    try:
        if account_id:
            data = Accounts.get(Accounts.id == account_id).to_dict()
        else:
            accounts = Accounts.select()
            data = [account.to_dict() for account in accounts]
    except Exception as error:
        return "error: {}".format(error), 400

    return jsonify(data)

@app.route('/api/accounts', methods=['POST'])
def api_post_account():
    try:
        req = request.get_json()
        res = Accounts.create(
            name=req['name'],
            password=hash_password(req['password'])
        )

    except Exception as error:
        return "error: {}".format(error), 400
    return "Successfully created a new account. ID: {}, Name: {}".format(res.id, res.name)

@app.route('/api/load/<int:account_id>', methods=['PATCH'])
def api_load_money(account_id):
    """Load money to account."""
    try:
        req = request.get_json()
        account = Accounts.get(Accounts.id == account_id)
        account.availableBalance += round(req['amount'], 2)
        account.ledgerBalance += round(req['amount'], 2)
        account.save()
        # insert transaction and transfer rows for the load amount
        # transaction type is 'load'
        transactionID = str(uuid.uuid1())
        res = Transactions.create(
            transactionID=transactionID,
            senderID=account_id,
            receiverID=account_id,
            amount=round(req['amount'], 2),
            transactionType=TRANSACTION_TYPES[2]
        )
        res = Transfer.create(
            account=account_id,
            transactionID=transactionID,
            amount=round(req['amount'], 2),
            presented=True
        )
    except Exception as error:
        return "error: {}".format(error), 400
    return "Successfully loaded {} € to account id: {}".format(req['amount'], account_id)

@app.route('/api/transactions/<int:transaction_id>')
@app.route('/api/transactions')
def api_get_transactions(transaction_id=None):
    data = None
    try:
        if transaction_id:
            data = Transactions.get(Transactions.id == transaction_id).to_dict()
        else:
            transactions = Transactions.select()
            data = [transaction.to_dict() for transaction in transactions]
    except Exception as error:
        return "error: {}".format(error), 400

    return jsonify(data)

@app.route('/api/transfers/<int:transfer_id>')
@app.route('/api/transfers')
def api_get_transfers(transfer_id=None):
    """Get all transfers."""
    data = None
    try:
        if transfer_id:
            data = Transfer.get(Transfer.id == transfer_id).to_dict()
        else:
            transfers = Transfer.select()
            data = [transfer.to_dict() for transfer in transfers]
    except Exception as error:
        return "error: {}".format(error), 400

    return jsonify(data)

@app.route('/api/transfers/account/<int:account_id>')
def api_get_account_transfers(account_id):
    """Dynamically calculate account balances from the transfer table."""
    data = None
    ledger_balance = 0
    available_balance = 0
    account = Accounts.get(Accounts.id == account_id)
    try:
        data = [transfer.to_dict() for transfer in Transfer.select().where(Transfer.account == account_id)]
        for item in data:
            if item['presented']:
                ledger_balance += round(item['amount'], 2)
            available_balance += round(item['amount'], 2)

    except Exception as error:
        return "error: {}".format(error), 400

    return jsonify({
        'accountID': account_id,
        'accountName': account.name,
        'ledgerBalance': round(ledger_balance, 2),
        'availableBalance': round(available_balance, 2),
        'transfers': data
    })


@app.route('/api/transactions', methods=['POST'])
def api_transactions():
    """Transaction API to send funds between two existing accounts."""
    try:
        req = request.get_json()
        # get sender and receiver from the database
        sender = Accounts.get(Accounts.id == req['senderID'])
        receiver = Accounts.get(Accounts.id == req['receiverID'])

        # if transaction is valid do the transaction
        if transaction_check(req, sender, receiver):
            # create new entry in the Transactions table
            res = Transactions.create(
                transactionID=req['transactionID'],
                senderID=req['senderID'],
                receiverID=req['receiverID'],
                amount=round(req['amount'], 2),
                transactionType=req['transactionType']
            )

            # if transaction type is authorization add entries to transfer table and subtract sender availableBalance
            if req['transactionType'] == TRANSACTION_TYPES[0]:
                sender.availableBalance -= round(req['amount'], 2)
                sender.save()
                insert_transfer(req, sender, receiver)
            else:
                # for presentment transaction update ledgerBalances for sender, receiver and bank accounts and update presentment = True for transfer
                for transfer in Transfer.select().where(Transfer.transactionID == req['transactionID']):
                    account = Accounts.get(Accounts.id == transfer.account.id)
                    account.ledgerBalance += round(transfer.amount, 2)
                    if account.id != sender.id:
                        account.availableBalance += round(transfer.amount, 2)
                    account.save()
                    transfer.presented = True
                    transfer.save()
        else:
            return "Transaction not valid", 403

    except Exception as error:
        return "error: {}".format(error), 400
    return "success, id: {}".format(res.id)

# Run Server
if __name__ == '__main__':
    app.run(debug=True, threaded=True)
