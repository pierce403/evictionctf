import requests

server='http://127.0.0.1:5000/'

response=requests.get(server+'flag?ioc=ninjas').text

print(response)

