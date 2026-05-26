import requests

url = 'http://localhost:5000'
r = requests.post(url, data={"pincode" : "1230"})
print(r.content)