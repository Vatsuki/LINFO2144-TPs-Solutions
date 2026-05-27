import requests

url = "http://localhost:5001/"

response = requests.post(url, data={"research":"get_flag"})
print(response.text)

