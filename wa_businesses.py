import requests
import json

accessToken = "<YOUR_FULL_ACCESS_TOKEN>"

endpoint = "https://gql.waveapps.com/graphql/public"
headers = {"Authorization": f"Bearer {accessToken}",
           "Content-Type": "application/json"}

query = """
query {
  businesses(page: 1, pageSize: 10) {
    pageInfo {
      currentPage
      totalPages
      totalCount
    }
    edges {
      node {
        id
        name
        isClassicAccounting
        isClassicInvoicing
        isPersonal
      }
    }
  }
}
         """

r = requests.post(
    endpoint, json={"query": query}, headers=headers)
print(json.dumps(r.json(), indent=2))
