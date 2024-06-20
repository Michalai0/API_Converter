# REQUEST
import requests

url = "https://swiftcodesapi.com/v1/swifts/UNILPKKA"

headers = {
    "Accept": "application/json",
    "X-Api-Key": "sk_7f023b55d0d681f5c88110eb1f9e52dec47086a75829a0e60c5a0ac5bd2f4e22"
}

response = requests.request("GET", url, headers=headers)

print(response.text)