# Online Bank

### API

| Route                               | Method | Purpose                                                    |
| ----------------------------------- |------  | ---------------------------------------------------------- |
| /api/accounts                       | GET    | Get all users                                              |
| /api/accounts/[account_id]          | GET    | Get single user with ID                                    |
| /api/accounts                       | POST   | Post new user. Fields: "name": str                         |
| /api/load/[account_id]              | PATCH  | Load funds to user. Fields: "amount": float                |
| /api/transactions                   | GET    | Get all transactions                                       |
| /api/transactions/[transaction_id]  | GET    | Get single transaction with transaction id                 |
| /api/transfers                      | GET    | Get all transfers                                          |
| /api/transfers/[transfer_id]        | GET    | Get single transfer with transfer id                       |
| /api/transfers/account/[account_id] | GET    | Get all transfers for single account with account id       |

### Functionalities

* Create new account, POST request /api/accounts
* Get accounts/account with account id
* Load money via /api/load/[account_id] route
* Get all transfers, single transfer, all transfers for user
* Get all transactions, single transaction
* Post new transactions (types: authorization, presentment, load)
