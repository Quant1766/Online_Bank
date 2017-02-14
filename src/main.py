
"""main app"""

from flask import Flask, request, jsonify
from models import *
import uuid

app = Flask(__name__)

# unique properties for the issuer
BANK_FEE_PERCENT = 1
BANK_NAME = 'Holvi'
BANK_ID = 3
MINIMUM_TRANSFER = 1.00

 # valid transaction types
TRANSACTION_TYPES = ['authorization', 'presentment', 'load']

# helper and utility functions
@app.before_request
def before_request():
    init_db()

@app.after_request
def after_request(response):
    close_db()
    return response

def transaction_check(req, sender, receiver):
    """Transaction validity check."""
    # if transaction type is 'presentment' check that previous authorization transaction can be found
    if req['transactionType'] == TRANSACTION_TYPES[1]:
        
        try:
            auth_transaction = Transactions.get(Transactions.transactionID == req['transactionID'])
            if auth_transaction.transactionID != req['transactionID']:
                print("2 hello: {}".format(auth_transaction.transactionID))
                return False
        except Exception:
            return False
    # check that the sender and receiver and the sent amount is valid (more than 0 and less than available balance)
    if sender.id == req['senderID'] and\
    receiver.id == req['receiverID'] and\
    float(req['amount']) >= MINIMUM_TRANSFER and\
    req['transactionType'] in TRANSACTION_TYPES and\
    sender.availableBalance >= float(req['amount']):
        return True
    return False

def insert_transfer(req, sender, receiver):
    """Insert non-presented entries to Transfer table, including bank fee entry.
        Transfer model (account_id + transactionID = unique constraint):
            account_id,
            transactionID,
            amount,
            presented
    """

    fee_amount = round(BANK_FEE_PERCENT * req['amount'] / 100.00, 2)
    #presented = 1 if req['transactionType'] == TRANSACTION_TYPES[1] else 0
    data = [
        {
            "account": sender.id,
            "transactionID": req['transactionID'],
            "amount": round(-req['amount'], 2)
        },
        {
            "account": receiver.id,
            "transactionID": req['transactionID'],
            "amount": round(req['amount']-fee_amount, 2)
        },
        {
            "account": BANK_ID,
            "transactionID": req['transactionID'],
            "amount": fee_amount
        }
    ]
    with db.atomic():
        Transfer.insert_many(data).execute()

# root
@app.route('/')
def root():
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
        return "error: {}".format(error), 401

    return jsonify(data)

@app.route('/api/accounts', methods=['POST'])
def api_post_account():
    try:
        req = request.get_json()
        res = Accounts.create(
            name=req['name']
        )

    except Exception as error:
        return "error: {}".format(error), 401
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
            amount=round(req["amount"], 2),
            presented=True
        )
    except Exception as error:
        return "error: {}".format(error), 401
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
        return "error: {}".format(error), 401

    return jsonify(data)

@app.route('/api/transfers/<int:transfer_id>')
@app.route('/api/transfers')
def api_get_transfers(transfer_id=None):
    data = None
    try:
        if transfer_id:
            data = Transfer.get(Transfer.id == transfer_id).to_dict()
        else:
            transfers = Transfer.select()
            data = [transfer.to_dict() for transfer in transfers]
    except Exception as error:
        return "error: {}".format(error), 401

    return jsonify(data)

@app.route('/api/transfers/account/<int:account_id>')
def api_get_account_transfers(account_id):
    data = None
    ledger_balance = 0
    available_balance = 0
    account = Accounts.get(Accounts.id == account_id)
    try:
        data = [transfer.to_dict() for transfer in Transfer.select().where(Transfer.account == account_id)]
        for item in data:
            if item["presented"]:
                ledger_balance += item["amount"]
                available_balance += item["amount"]
            else:
                available_balance += item["amount"]

    except Exception as error:
        return "error: {}".format(error), 401

    return jsonify({
        'accountID': account_id,
        'accountName': account.name,
        'ledgerBalance': ledger_balance,
        'availableBalance': available_balance,
        'transfers': data
    })


@app.route('/api/transactions', methods=['POST'])
def api_transactions():
    """Transaction API to send funds between accounts."""
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

            # if transaction type is authorization add entries to transfer table and subtrack sender availableBalance
            if req['transactionType'] == TRANSACTION_TYPES[0]:
                sender.availableBalance -= req['amount']
                sender.save()
                insert_transfer(req, sender, receiver)
            else:
                # for presentment transaction update ledgerBalances for sender, receiver and bank accounts and update presentment = True for transfer
                for transfer in Transfer.select().where(Transfer.transactionID == req['transactionID']):
                    account = Accounts.get(Accounts.id == transfer.account.id)
                    account.ledgerBalance += transfer.amount
                    if account.id != sender.id:
                        account.availableBalance += transfer.amount
                    account.save()
                    transfer.presented = True
                    transfer.save()
        else:
            return "Transaction not valid", 403

    except Exception as error:
        return "error: {}".format(error), 401
    return "success, id: {}".format(res.id)

# Run Server
if __name__ == '__main__':
    app.run(debug=True, threaded=True)
