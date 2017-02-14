# Online Bank

### API

| Route                      | Method | Purpose                                 |
| -------------------------- |------  | --------------------------------------- |
| /api/accounts              | GET    | Get all users                           |
| /api/accounts/[account_id] | GET    | Get single user with ID                 |
| /api/accounts              | POST   | Post new user. Fields: "name": str      |

### Functionalities

* Create new account, POST request /api/accounts
* Get accounts/account with account id
* Load money via /api/load/[account_id] route
* Get all transfers, single transfer, all transfers for user
* Get all transactions, single transaction
* Post new transactions (types: authorization, presentment, load)
