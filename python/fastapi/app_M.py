import requests

url = "https://apis.openapi.sk.com/transit/routes/sub"

payload = {
    "startX": "127.020823989335",
    "startY": "37.5569959545519",
    "endX": "126.997040336091",
    "endY": "37.5256637737053",
    "format": "json",
    "count": 5
}
headers = {
    "accept": "application/json",
    "appKey": "I2ODVii4Zs4NUgMXaBKhE3Rjc5I6r7WRvLa3R8xc",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

# 가장 작은 totalTime을 가진 경로 찾기
min_total_time = float('inf')
best_route = None
print("Response status code:", response.status_code)

for route in data['metaData']['plan']['itineraries']:
    if route['totalTime'] < min_total_time:
        min_total_time = route['totalTime']
        best_route = route

print("가장 짧은 totalTime:", min_total_time)
print("가장 짧은 경로:", best_route)