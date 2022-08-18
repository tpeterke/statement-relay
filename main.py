import os
import sys
import base64
import json
import rsa
import requests
import urllib3
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
import pytz
from google.cloud import secretmanager



tw_private_key_path = 'tw_private_pem'
config_path = 'tw_config_json'
tw_base_url = 'https://api.transferwise.com'
wa_endpoint = "https://gql.waveapps.com/graphql/public"
wa_token = 'please have it in secret'
tw_token = 'please have it in secret'
project_id = os.environ["GCP_PROJECT"]
client = secretmanager.SecretManagerServiceClient()

mutation = """
  mutation ($input: MoneyTransactionCreateInput!){
    moneyTransactionCreate(input: $input){
      didSucceed
      inputErrors {
        path
        message
        code
      }
      transaction {
        id
      }
    }
  }
"""

http = urllib3.PoolManager()


def get_statement(one_time_token, signature, profile_id, account_id, currency):
    interval_start = (datetime.now(timezone.utc) -
                      timedelta(days=10)).isoformat()
    interval_end = datetime.now(timezone.utc).isoformat()

    params = urlencode({
        'currency': currency, 'type': 'FLAT',  # 'COMPACT'
        'intervalStart': interval_start,
        'intervalEnd': interval_end})

    url = (
        tw_base_url + '/v3/profiles/' + profile_id + '/borderless-accounts/'
        + account_id + '/statement.json?' + params)

    headers = {
        'Authorization': 'Bearer ' + tw_token,
        'User-Agent': 'tw-statements-sca',
        'Content-Type': 'application/json'}
    if one_time_token != "":
        headers['x-2fa-approval'] = one_time_token
        headers['X-Signature'] = signature
        print(headers['x-2fa-approval'], headers['X-Signature'])

    r = http.request('GET', url, headers=headers, retries=False)

    if r.status == 200 or r.status == 201:
        return json.loads(r.data)
    elif r.status == 403 and r.getheader('x-2fa-approval') is not None:
        one_time_token = r.getheader('x-2fa-approval')
        signature = do_sca_challenge(one_time_token)
        get_statement(one_time_token, signature,
                      profile_id, account_id, currency)
    else:
        print('failed: ', r.status)
        print(json.dumps(json.loads(r.data), indent=2))
        sys.exit(0)


def do_sca_challenge(one_time_token):
    print('doing sca challenge')

    # Read the private key file as bytes.
    private_key_data = get_secrets(tw_private_key_path)
    if not private_key_data:
        sys.exit(0)

    private_key = rsa.PrivateKey.load_pkcs1(private_key_data, 'PEM')

    # Use the private key to sign the one-time-token that was returned
    # in the x-2fa-approval header of the HTTP 403.
    signed_token = rsa.sign(
        one_time_token.encode('ascii'),
        private_key,
        'SHA-256')

    # Encode the signed message as friendly base64 format for HTTP
    # headers.
    signature = base64.b64encode(signed_token).decode('ascii')

    return signature


def get_secrets(secret_request):
    l_secret = ""
    name = f"projects/{project_id}/secrets/{secret_request}/versions/latest"
    try:
        response = client.access_secret_version(name=name)
        l_secret = response.payload.data.decode("UTF-8") 
        print(secret_request, "determined through secret")
    except:
        pass

    if l_secret == "" or l_secret == None:
        try:
            l_secret = os.getenv(secret_request)
            if l_secret != "" and l_secret != None:
                print(secret_request, "determined from environment")
        except:
            pass

    if l_secret == "" or l_secret == None:
        try:
            with open("./"+secret_request, 'rb') as f:
                l_secret = f.read()
            if l_secret != "" and l_secret != None:
                print(secret_request, "determined from file")
        except:
            pass

    if l_secret == "" or l_secret == None:
        print("Determining", secret_request, "was not successful")

    return l_secret

def main(args):
    global tw_token
    global wa_token

    wa_token = get_secrets("WA_TOKEN")
    if not wa_token:
        sys.exit(0)

    tw_token = get_secrets("TW_TOKEN")
    if not tw_token:
        sys.exit(0)

    wa_headers = {"Authorization": f"Bearer {wa_token}",
                'Content-Type': 'application/json'}

    # Get config from file (config.json)
    config = get_secrets(config_path)
    if not config:
        sys.exit(0)
    try:
        config = json.loads(config)
    except:
        pass    #works only if config was str. if loaded json, that cannot be converted to json

    for transfer in config["transfers"]:
        if transfer["type"] == "transferwise":
            statement = get_statement("", "",
                                      transfer["from"]["profileId"],
                                      transfer["from"]["accountId"],
                                      transfer["from"]["currency"])

            if statement is not None and 'currency' in statement['request']:
                currency = statement['request']['currency']
                bname = statement['accountHolder']['type']
                if statement['accountHolder']['type'] == 'PERSONAL':
                    bname = bname + " " + statement['accountHolder']['firstName'] + \
                        " " + statement['accountHolder']['lastName']
                else:
                    bname = bname + " " + \
                        statement['accountHolder']['businessName']
            else:
                print('something is wrong')
                print(statement)
                sys.exit(0)

            if 'transactions' in statement:
                txns = len(statement['transactions'])
                print(bname, currency, 'statement received with',
                      txns, 'transactions.')
# Insert to WA
                num_succ = 0
                num_dupl = 0
                num_other_err = 0
                for transaction in statement["transactions"]:
                    dt = datetime.fromisoformat(
                        transaction["date"][:19] + "+00:00")
                    dt = dt.astimezone(pytz.timezone(
                        transfer["to"]["timezone"]))
                    variables = {
                        "input": {
                            "businessId": transfer["to"]["businessId"],
                            # "externalId": "test-" + transaction["referenceNumber"] + datetime.now().isoformat(),
                            "externalId": transaction["referenceNumber"],
                            "date": dt.isoformat()[:10],
                            "description": transaction["details"]["description"],
                            "anchor": {
                                "accountId": transfer["to"]["accountId"],
                                "amount": abs(float(transaction["amount"]["value"])),
                                "direction": "DEPOSIT"
                            },
                            "notes": "Transfer reference: " + transaction["referenceNumber"],
                            "lineItems": [{
                                "accountId": transfer["to"]["lineItemIdDeposit"],
                                "amount": abs(float(transaction["amount"]["value"])),
                                "balance": "INCREASE"
                            }]
                        }
                    }
                    if transaction["details"]["type"] == "DEPOSIT":
                        variables['input']['notes'] = variables['input']['notes'] + \
                            "\nSender Name: " + transaction["details"]["senderName"] + \
                            "\nSender Account: " + \
                            transaction["details"]["senderAccount"]
                        try:
                            if transaction["details"]["paymentReference"] != "":
                                variables['input']['notes'] = variables['input']['notes'] + \
                                    "\nPayment reference: " + \
                                    transaction["details"]["paymentReference"]
                        except:
                            pass
                    elif transaction["details"]["type"] == "MONEY_ADDED":
                        pass
                    elif transaction["details"]["type"] == "CONVERSION":
                        variables['input']['notes'] = variables['input']['notes'] + \
                            "\nCurrency conversion\nSource: " + str(transaction["details"]["sourceAmount"]["value"]) + " " + transaction["details"]["sourceAmount"]["currency"] + \
                            "\nTarget: " + str(transaction["details"]["targetAmount"]["value"]) + " " + transaction["details"]["targetAmount"]["currency"] + \
                            "\nRate: " + str(transaction["details"]["rate"])
                        # In case of conversion the same reference is being used in both accounts --> Waveapp will reject
                        variables["input"]["externalId"] = variables["input"]["externalId"] + \
                            "-" + transaction["amount"]["currency"]
                    elif transaction["details"]["type"] == "DIRECT_DEBIT":
                        variables['input']['notes'] = variables['input']['notes'] + \
                            "\nDirect Debit\nOriginated from: " + transaction["details"]["originator"] + \
                            "\nPayment reference: " + \
                            transaction["details"]["paymentReference"]
                        variables['input']['anchor']['direction'] = "WITHDRAWAL"
                        # variables['input']['lineItems'][0]['balance'] = "DECREASE"
                        variables['input']['lineItems'][0]['accountId'] = transfer["to"]["lineItemIdWithdraw"]
                    else:  # "TRANSFER" or "CARD"
                        try:
                            variables['input']['notes'] = variables['input']['notes'] + \
                                "\nRecipient's Name: " + transaction["details"]["recipient"]["name"] + \
                                "\nRecipient's Account: " + \
                                transaction["details"]["recipient"]["bankAccount"]
                        except:
                            pass
                        try:
                            variables['input']['notes'] = variables['input']['notes'] + \
                                "\nRecipient's Name: " + transaction["details"]["merchant"]["name"] + \
                                "\n" + \
                                transaction["details"]["cardLastFourDigits"] + \
                                " - " + \
                                transaction["details"]["cardHolderFullName"]
                        except:
                            pass

                        variables['input']['anchor']['direction'] = "WITHDRAWAL"
                        # variables['input']['lineItems'][0]['balance'] = "DECREASE"
                        variables['input']['lineItems'][0]['accountId'] = transfer["to"]["lineItemIdWithdraw"]
                    if "WISE" in transaction["details"]["description"].upper() and "CHARGES" in transaction["details"]["description"].upper():
                        # this is a fee and the reference is the same as the original transaction --> Waveapp will reject
                        variables["input"]["externalId"] = variables["input"]["externalId"] + "/Fee"
                    if transaction["type"] == "DEBIT":
                        variables['input']['anchor']['direction'] = "WITHDRAWAL"
                        variables['input']['lineItems'][0]['accountId'] = transfer["to"]["lineItemIdWithdraw"]
                    else:
                        variables['input']['anchor']['direction'] = "DEPOSIT"
                        variables['input']['lineItems'][0]['accountId'] = transfer["to"]["lineItemIdDeposit"]

                    # print(variables)

                    r = requests.post(
                        wa_endpoint, json={"query": mutation, "variables": variables}, headers=wa_headers)
                    if r.status_code != 200 and r.status_code != 201:
                        print(json.dumps(r.json(), indent=2))
                    else:
                        succeeded = False
                        try:
                            succeeded = r.json()[
                                'data']['moneyTransactionCreate']['didSucceed']
                        except:
                            print(json.dumps(json.loads(r.text), indent=2))
                        if succeeded:
                            num_succ = +1
                        elif 'same externalId' in r.text:
                            num_dupl = + 1
                        else:
                            num_other_err = + 1
                print(bname, currency, " uploaded ", num_succ, " transactions, seen ", num_dupl,
                      " duplicate transactions and experienced ", num_other_err, " other errors.")
            else:
                print(f'Empty statement for {currency} currency')
                sys.exit(0)
