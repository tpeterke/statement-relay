import requests
import json


accessToken = "<YOUR_FULL_ACCESS_TOKEN>"

endpoint = "https://gql.waveapps.com/graphql/public"
headers = {"Authorization": f"Bearer {accessToken}",
           "Content-Type": "application/json"}

query = """
query ($businessId: ID!) {
  business(id: $businessId) {
    id
    accounts(page: 1, pageSize: 100, subtypes: [UNCATEGORIZED_EXPENSE,UNCATEGORIZED_INCOME,CASH_AND_BANK]) {
      pageInfo {
        currentPage
        totalPages
        totalCount
      }
      edges {
        node {
          id
          name
          description
          displayId
          currency {
              code
          }
          type {
            name
            value
          }
          subtype {
            name
            value
          }
          normalBalanceType
          isArchived
        }
      }
    }
  }
}
         """

variables = """
{
    "businessId": "<YOUR_BUSINESS_ID>"
}
"""


r = requests.post(
    endpoint, json={"query": query, "variables": variables}, headers=headers)
print(json.dumps(r.json(), indent=2))
