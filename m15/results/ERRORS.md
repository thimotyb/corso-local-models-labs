# Hand-written tickets answered wrongly

Tickets 100 to 119 are written to be hard. One row per wrong answer; the confidence is that of the wrong top answer.

## opendecider-nano (6 wrong answers)

| id | question | correct | answered | confidence | ticket |
|---|---|---|---|---|---|
| 105 | urgent | True | False | 0.71 | Quote needed for 50 seats; the board votes this afternoon. |
| 109 | refund | False | True | 0.54 | Wrong amount on invoice 88, my accountant needs the corrected one by end of day. |
| 111 | urgent | True | False | 0.53 | The API key stopped working during a demo to our client in 30 minutes. |
| 113 | urgent | False | True | 0.62 | Please cancel my subscription and refund this month; I noticed it only today. |
| 118 | team | sales | engineering | 0.36 | We need an urgent contract amendment before the signing at 5 pm. |
| 119 | refund | False | True | 0.55 | I got a refund for the wrong order; please correct it, no rush. |

## xgboost-tfidf (26 wrong answers)

| id | question | correct | answered | confidence | ticket |
|---|---|---|---|---|---|
| 100 | team | billing | sales | 0.85 | I do not want a refund, I want the double charge on order 5521 explained. Next week is fine. |
| 101 | team | billing | sales | 0.55 | The refund you promised last month has still not arrived, and the bank closes my account tomorrow. |
| 101 | urgent | True | False | 0.94 | The refund you promised last month has still not arrived, and the bank closes my account tomorrow. |
| 102 | team | engineering | billing | 0.75 | Our checkout is down right now and we are losing sales every minute. |
| 102 | urgent | True | False | 0.92 | Our checkout is down right now and we are losing sales every minute. |
| 103 | team | engineering | sales | 0.75 | Could your engineers look at the slow dashboard when they get a chance? No refund needed. |
| 103 | refund | False | True | 0.79 | Could your engineers look at the slow dashboard when they get a chance? No refund needed. |
| 104 | team | billing | sales | 0.88 | We were overcharged, please credit it back to our card. |
| 104 | refund | True | False | 0.77 | We were overcharged, please credit it back to our card. |
| 108 | team | engineering | sales | 0.38 | The app crashes at payment. I want to cancel the order and get my money back, immediately. |
| 108 | urgent | True | False | 0.98 | The app crashes at payment. I want to cancel the order and get my money back, immediately. |
| 109 | team | billing | engineering | 0.57 | Wrong amount on invoice 88, my accountant needs the corrected one by end of day. |
| 109 | urgent | True | False | 0.97 | Wrong amount on invoice 88, my accountant needs the corrected one by end of day. |
| 110 | team | billing | sales | 0.63 | I would like to return the product and get a refund; there is no hurry. |
| 111 | team | engineering | sales | 0.71 | The API key stopped working during a demo to our client in 30 minutes. |
| 111 | urgent | True | False | 0.80 | The API key stopped working during a demo to our client in 30 minutes. |
| 112 | team | sales | billing | 0.67 | Do you have a student discount? I am not in a hurry. |
| 114 | team | engineering | sales | 0.74 | The reset email never arrives and I am locked out before tomorrow's audit. |
| 114 | urgent | True | False | 0.64 | The reset email never arrives and I am locked out before tomorrow's audit. |
| 115 | team | sales | billing | 0.78 | Interested in your enterprise offer, can someone call me this week? |
| 116 | team | billing | sales | 0.72 | You charged my card 3 times! Fix this now and refund two of them. |
| 116 | urgent | True | False | 0.85 | You charged my card 3 times! Fix this now and refund two of them. |
| 117 | team | engineering | sales | 0.86 | The export button does nothing since the last update. |
| 118 | urgent | True | False | 0.94 | We need an urgent contract amendment before the signing at 5 pm. |
| 119 | team | billing | engineering | 0.58 | I got a refund for the wrong order; please correct it, no rush. |
| 119 | refund | False | True | 0.98 | I got a refund for the wrong order; please correct it, no rush. |
