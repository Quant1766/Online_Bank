# Online Bank

Python 3 Flask REST API web application (with peewee ORM + SQLite) to demonstrate some of the concepts of online banking.

### API

| Route                               | Method | Purpose                                                    |
| ----------------------------------- |------  | ---------------------------------------------------------- |
| /api/accounts                       | GET    | Get all users                                              |
| /api/accounts/[account_id]          | GET    | Get single user with ID                                    |
| /api/accounts                       | POST   | Post new user. Fields: "name": str                         |
| /api/load/[account_id]              | PATCH  | Load funds to user. Fields: "amount": float                |
| /api/transactions                   | GET    | Get all transactions                                       |
| /api/transactions/[transaction_id]  | GET    | Get single transaction with transaction id                 |
| /api/transactions                   | POST   | Post new transaction (see details below)                   |
| /api/transfers                      | GET    | Get all transfers                                          |
| /api/transfers/[transfer_id]        | GET    | Get single transfer with transfer id                       |
| /api/transfers/account/[account_id] | GET    | Get all transfers for single account with account id       |

### Concepts
This application only accepts transactions between two accounts that exist in the Accounts table. Application doesn't have the Scheme implemented or batch job to transfer money to the scheme. There is no authentication either!

Bank takes 1 % fee for all transactions from the sender. So if sender (account 1) sends 10 € to account 2, bank takes 1 % of 10 € from the transfer amount and the account 2 only gets 9.9 € and the bank gets 0.1 €. Bank fee is defined as a global variable.

You first must make two accounts and third account is the bank itself (account id 3)! You can change this bank id from the global variable.

Minimum transfer amount is 1 €

This application doesn't have currency implemented. Funds are just floats.

### Functionalities

* Create new account, POST request /api/accounts
* Get accounts/account with account id
* Load money via /api/load/[account_id] route
* Get all transfers, single transfer, all transfers for user
* Get all transactions, single transaction
* Post new transactions (types: authorization, presentment, load)

### Transactions
To make a new transaction you must first send JSON data to route: ```/api/transactions``` with transactionType == 'authorization' to reserve funds from the cardholders account. Second transaction call to same route must: transactionType == 'presentment' that actually deduct the funds from the account. **Notice that minimum transaction amount is 1 €.**

Example data:
```
{
	'senderID': 1,
	'receiverID': 2,
	'amount': 10.00,
	'transactionType': 'authorization',
	'transactionID': '1234ZORRO'
}
```
### Load money
You can load money to accounts with route: ```/api/load/<account_id>``` where account_id is your desired account id integer.
Example data to send as PATCH method to the API:
```
{
	'amount': 10.00
}
```
