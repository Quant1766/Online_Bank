# with this function you can make transactions to the API endpoint

function Invoke-Transaction {
    param(
        [int]$SenderID = 1,
        [int]$ReceiverID = 2,
        [float]$Amount = 10.0,
        [string]$TransactionID,
        [ValidateSet('authorization', 'presentment')]
        [string]$TransactionType
    )
    $transactionURL = "http://127.0.0.1:5000/api/transactions"
    $ct = "application/json"

    $body = @{
        senderID = $SenderID
        receiverID = $ReceiverID
        amount = $Amount
        transactionType = $TransactionType
        transactionID = $TransactionID
    } | ConvertTo-Json

    Invoke-RestMethod -Uri $transactionURL -Method Post -Body $body -ContentType $ct
}

Invoke-Transaction -TransactionType presentment -TransactionID abc123 -Amount 1.0 -SenderID 1 -ReceiverID 2