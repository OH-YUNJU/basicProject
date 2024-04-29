from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
import requests
from typing import Union
from typing import Optional
from bson.objectid import ObjectId
import os.path
import json
from pymongo import mongo_client
import pydantic
import math
from database import db_conn
from models import Housing_data, Place_coordinates
pydantic.json.ENCODERS_BY_TYPE[ObjectId] = str

app = FastAPI()

db = db_conn()
session = db.sessionmaker()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.relpath("./")))
secret_file = os.path.join(BASE_DIR, '../secret.json')

with open(secret_file) as f:
    secrets = json.loads(f.read())
    
def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        errorMsg = "Set the {} environment variable.".format(setting)

KAKAOAPI = get_secret("kakao_apiKey")
USERNAME = get_secret("username")
PASSWORD = get_secret("password")
HOSTNAME = get_secret("hostname")
TMAPAPI = get_secret("TMAP_apiKey")

client = mongo_client.MongoClient(f'mongodb://{USERNAME}:{PASSWORD}@{HOSTNAME}')

mydb = client['basicPJ']
rentdb = mydb['rent']

base_url = 'http://192.168.1.98:5000/rent'


def search_address(address):
    url = 'https://dapi.kakao.com/v2/local/search/address.json'
    headers = {
        'Authorization': f'KakaoAK {KAKAOAPI}',
    }
    params = {
        'query': address,
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get('documents'):
            first_document = data['documents'][0]
            x_coordinate = first_document.get('x')
            y_coordinate = first_document.get('y')
            return x_coordinate, y_coordinate
        else:
            print('No documents found')
            return None
    else:
        print(f'Error: {response.status_code}')
        return None

def getXYBound(x, y):
  # 5km 구간
  x = float(x)
  y = float(y)
  x_change = 5 / 111.2
  y_change = abs(math.cos(x * (math.pi / 180)))
  bounds = {
    "firstx": x - x_change,
    "firsty": y - y_change,
    "secondx": x + x_change,
    "secondy": y + y_change
  }
  return bounds

def getTime(oftenx, ofteny, wantx, wanty):
    url = "https://apis.openapi.sk.com/transit/routes/sub"

    payload = {
        "startX": oftenx,
        "startY": ofteny,
        "endX": wantx,
        "endY": wanty,
        "format": "json",
        "count": 5
    }
    headers = {
        "accept": "application/json",
        "appKey": TMAPAPI,
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    try : 
        # 가장 작은 totalTime을 가진 경로 찾기
        min_total_time = float('inf')
        best_route = None
        print("Response status code:", response.status_code)

        for route in data['metaData']['plan']['itineraries']:
            if route['totalTime'] < min_total_time:
                min_total_time = route['totalTime']
                best_route = route
    except KeyError as e:
        return ("Status: 400")
    
    min_total_time = int(min_total_time/60)
    return {"min_total_time": min_total_time}

#####################################################################


@app.get(path='/rent')
async def rent():
    response = requests.get(base_url)
    if response:
        return "OK"
    else:
        "NOT FOUND"

@app.get("/rent/select-address")
async def rent_selectAddress():
    params = '?HOUSE_GBN_NM=아파트&HOUSE_GBN_NM=연립다세대&HOUSE_GBN_NM=오피스텔'
    #params = f'?HOUSE_GBN_NM={HOUSE_GBN_NM}'
    url = base_url + params
     
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            first_entry = data[0]
            selected_data = {
                "STATUS": 200,
                "RESULT": {
                    "SGG_NM": first_entry.get("SGG_NM"),
                    "BJDONG_NM": first_entry.get("BJDONG_NM"),
                    "BOBN": first_entry.get("BOBN"),
                    "BUBN": first_entry.get("BUBN"),
                    "RENT_GBN": first_entry.get("RENT_GBN"),
                    "RENT_GTN": first_entry.get("RENT_GTN"),
                    "RENT_FEE": first_entry.get("RENT_FEE"),
                    "BLDG_NM": first_entry.get("BLDG_NM"),
                    "HOUSE_GBN_NM": first_entry.get("HOUSE_GBN_NM"),
                    "RENT_AREA": first_entry.get("RENT_AREA")
                }
            }
            return selected_data
        else:
            raise HTTPException(status_code=400, detail={"STATUS": 400})
    else:
        raise HTTPException(status_code=400, detail={"STATUS": 400})
        
@app.get("/rent/find-coordinate")
async def rent_findCoordinate():
    params = '?HOUSE_GBN_NM=아파트&HOUSE_GBN_NM=연립다세대&HOUSE_GBN_NM=오피스텔'
    url = base_url + params
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            first_entry = data[0]
            SGG_NM = first_entry.get("SGG_NM")
            BJDONG_NM = first_entry.get("BJDONG_NM")
            BOBN = first_entry.get("BOBN")
            BUBN = first_entry.get("BUBN")
            
            address = f"{SGG_NM} {BJDONG_NM} {BOBN}-{BUBN}"
            
            coordinates = search_address(address)
            
            if coordinates:
                x, y = coordinates
                
            selected_data = {
                "STATUS": 200,
                "RESULT": {
                    "SGG_NM": SGG_NM,
                    "BJDONG_NM": BJDONG_NM,
                    "BOBN": BOBN,
                    "BUBN": BUBN,
                    "BLDG_NM": first_entry.get("BLDG_NM"),
                    "x": x,
                    "y": y
                }
            }
            return selected_data
        else:
            raise HTTPException(status_code=400, detail={"STATUS": 400})
    else:
        raise HTTPException(status_code=400, detail={"STATUS": 400})
    
@app.post('/rent/insert-coordinate')
async def rent_insertCoordinate():
    params = '?HOUSE_GBN_NM=아파트&HOUSE_GBN_NM=연립다세대&HOUSE_GBN_NM=오피스텔'
    url = base_url + params
    response = requests.get(url)

    if response.status_code == 200:
        tmp = 0
        data = response.json()
        if data:
            for entry in data:
                SGG_NM = entry.get("SGG_NM")
                BJDONG_NM = entry.get("BJDONG_NM")
                BOBN = entry.get("BOBN")
                BUBN = entry.get("BUBN")
                RENT_GBN = entry.get("RENT_GBN")
                RENT_GTN = entry.get("RENT_GTN")
                RENT_FEE = entry.get("RENT_FEE")
                BLDG_NM = entry.get("BLDG_NM")
                HOUSE_GBN_NM = entry.get("HOUSE_GBN_NM")
                RENT_AREA = entry.get("RENT_AREA")
                
                address = f"{SGG_NM} {BJDONG_NM} {BOBN}-{BUBN}"
                coordinates = search_address(address)
                
                if coordinates:
                    x, y = coordinates
                    result = {
                        "SGG_NM": SGG_NM,
                        "BJDONG_NM": BJDONG_NM,
                        "BOBN": BOBN,
                        "BUBN": BUBN,
                        "RENT_GBN": RENT_GBN,
                        "RENT_GTN": RENT_GTN,
                        "RENT_FEE": RENT_FEE,
                        "BLDG_NM": BLDG_NM,
                        "HOUSE_GBN_NM": HOUSE_GBN_NM,
                        "RENT_AREA": RENT_AREA,
                        "x": x,
                        "y": y
                    }
                    rentdb.insert_one(result)
                    tmp += 1
                    
            return {"STATUS": 200,"RESULT": {"MESSAGE": "All data inserted successfully", "COUNT": tmp}}
        else:
            raise HTTPException(status_code=400, detail={"STATUS": 400,"RESULT": {"MESSAGE": "No data to insert."}})
    else:
        raise HTTPException(status_code=400, detail={"STATUS": 400,"RESULT": {"MESSAGE": "Failed to fetch data from API."}})
    
    
#########################################################



@app.get('/rent/insert-monthArea-up')
async def rent_insertMonthAreaUp():
    RENT_AREA = 33
    RENT_GBN = "월세"

    filter_criteria = {
        "RENT_AREA": {"$gt": RENT_AREA},
        "RENT_GBN": RENT_GBN
    }

    results = rentdb.find(filter_criteria, {"_id": 0})
     
    new_collection = mydb['monthAreaUp']

    count = 0
    for document in results:
        if 'RENT_GTN' in document:
            document['RENT_GTN'] = float(document['RENT_GTN'])
        if 'RENT_FEE' in document:
            document['RENT_FEE'] = float(document['RENT_FEE'])
        if 'RENT_AREA' in document:
            document['RENT_AREA'] = float(document['RENT_AREA'])
        if 'x' in document:
            document['x'] = float(document['x'])
        if 'y' in document:
            document['y'] = float(document['y']) 
        
        new_collection.insert_one(document)
        count += 1

    return {"STATUS": 200, "RESULT": {"MESSAGE": "Data saved successfully", "COUNT": count}}

@app.get('/rent/insert-yearArea-up')
async def rent_insertYearAreaUp():
    RENT_AREA = 33
    RENT_GBN = "전세"

    filter_criteria = {
        "RENT_AREA": {"$gt": RENT_AREA},
        "RENT_GBN": RENT_GBN
    }

    results = rentdb.find(filter_criteria, {"_id": 0})

    new_collection = mydb['yearAreaUp']

    count = 0
    for document in results:
        if 'RENT_GTN' in document:
            document['RENT_GTN'] = float(document['RENT_GTN'])
        if 'RENT_FEE' in document:
            document['RENT_FEE'] = float(document['RENT_FEE'])
        if 'RENT_AREA' in document:
            document['RENT_AREA'] = float(document['RENT_AREA'])
        if 'x' in document:
            document['x'] = float(document['x'])
        if 'y' in document:
            document['y'] = float(document['y']) 
        
        new_collection.insert_one(document)
        count += 1

    return {"STATUS": 200, "RESULT": {"MESSAGE": "Data saved successfully", "COUNT": count}}

@app.get('/rent/insert-monthArea-dw')
async def rent_insertMonthAreaDw():
    RENT_AREA = 33
    RENT_GBN = "월세"

    filter_criteria = {
        "RENT_AREA": {"$lt": RENT_AREA},
        "RENT_GBN": RENT_GBN
    }

    results = rentdb.find(filter_criteria, {"_id": 0})

    new_collection = mydb['monthAreaDw']

    count = 0
    for document in results:
        if 'RENT_GTN' in document:
            document['RENT_GTN'] = float(document['RENT_GTN'])
        if 'RENT_FEE' in document:
            document['RENT_FEE'] = float(document['RENT_FEE'])
        if 'RENT_AREA' in document:
            document['RENT_AREA'] = float(document['RENT_AREA'])
        if 'x' in document:
            document['x'] = float(document['x'])
        if 'y' in document:
            document['y'] = float(document['y']) 
        
        new_collection.insert_one(document)
        count += 1

    return {"STATUS": 200, "RESULT": {"MESSAGE": "Data saved successfully", "COUNT": count}}

@app.get('/rent/insert-yearArea-dw')
async def rent_insertYearAreaDw():
    RENT_AREA = 33
    RENT_GBN = "전세"

    filter_criteria = {
        "RENT_AREA": {"$lt": RENT_AREA},
        "RENT_GBN": RENT_GBN
    }

    results = rentdb.find(filter_criteria, {"_id": 0})

    new_collection = mydb['yearAreaDw']

    count = 0
    for document in results:
        if 'RENT_GTN' in document:
            document['RENT_GTN'] = float(document['RENT_GTN'])
        if 'RENT_FEE' in document:
            document['RENT_FEE'] = float(document['RENT_FEE'])
        if 'RENT_AREA' in document:
            document['RENT_AREA'] = float(document['RENT_AREA'])
        if 'x' in document:
            document['x'] = float(document['x'])
        if 'y' in document:
            document['y'] = float(document['y']) 
        
        new_collection.insert_one(document)
        count += 1

    return {"STATUS": 200, "RESULT": {"MESSAGE": "Data saved successfully", "COUNT": count}}

@app.get('/rent/insertall')
async def rent_insertAll():
    result1 = await rent_insertMonthAreaUp()
    result2 = await rent_insertYearAreaUp()
    result3 = await rent_insertMonthAreaDw()
    result4 = await rent_insertYearAreaDw()
    
    return {"insertMonthAreaUp":result1, "insertYearAreaUp":result2, "insertMonthAreaDw":result3, "insertYearAreaDw":result4}

@app.delete('/rent/deleteall')
async def rent_deleteAll():
    mydb['monthAreaUp'].delete_many({})
    mydb['yearAreaUp'].delete_many({})
    mydb['monthAreaDw'].delete_many({})
    mydb['yearAreaDw'].delete_many({})

    month_area_up_count = mydb['monthAreaUp'].count_documents({})
    year_area_up_count = mydb['yearAreaUp'].count_documents({})
    month_area_dw_count = mydb['monthAreaDw'].count_documents({})
    year_area_dw_count = mydb['yearAreaDw'].count_documents({})

    return {
        "STATUS": 200,
        "RESULT": {
            "MESSAGE": "All content deleted",
            "COUNTS": {
                "monthAreaUp": month_area_up_count,
                "yearAreaUp": year_area_up_count,
                "monthAreaDw": month_area_dw_count,
                "yearAreaDw": year_area_dw_count
            }
        }
    }
    
@app.get('/rent/get-month-upavg')
async def rent_getMonthUpAvg(firstx: float, secondx: float, firsty: float, secondy: float):
    rent_collection = mydb['monthAreaUp']
    filter_criteria = {
        "x": {"$gte": firstx, "$lte": secondx},
        "y": {"$gte": firsty, "$lte": secondy},
    }
    
    rent_data = rent_collection.aggregate([
        {"$match": filter_criteria},
        {
            "$group": {
                "_id": None,
                "total_RENT_GTN": {"$sum": "$RENT_GTN"},
                "total_RENT_FEE": {"$sum": "$RENT_FEE"},
                "count": {"$sum": 1}
            }
        }
    ])
    rent_data = list(rent_data)
    if rent_data:
        total_RENT_GTN = rent_data[0]['total_RENT_GTN']
        total_RENT_FEE = rent_data[0]['total_RENT_FEE']
        count = rent_data[0]['count']
        avg_RENT_GTN = total_RENT_GTN / count
        avg_RENT_FEE = total_RENT_FEE / count
        return {
            "STATUS": 200,
            "RESULT": {
                "average_RENT_GTN": avg_RENT_GTN,
                "average_RENT_FEE": avg_RENT_FEE
            }
        }
    else:
        raise HTTPException(status_code=400)
    
@app.get('/rent/get-month-dwavg')
async def rent_getMonthDwAvg(firstx: float, secondx: float, firsty: float, secondy: float):
    rent_collection = mydb['monthAreaDw']
    filter_criteria = {
        "x": {"$gte": firstx, "$lte": secondx},
        "y": {"$gte": firsty, "$lte": secondy},
    }
    
    rent_data = rent_collection.aggregate([
        {"$match": filter_criteria},
        {
            "$group": {
                "_id": None,
                "total_RENT_GTN": {"$sum": "$RENT_GTN"},
                "total_RENT_FEE": {"$sum": "$RENT_FEE"},
                "count": {"$sum": 1}
            }
        }
    ])
    rent_data = list(rent_data)
    if rent_data:
        total_RENT_GTN = rent_data[0]['total_RENT_GTN']
        total_RENT_FEE = rent_data[0]['total_RENT_FEE']
        count = rent_data[0]['count']
        avg_RENT_GTN = total_RENT_GTN / count
        avg_RENT_FEE = total_RENT_FEE / count
        return {
            "STATUS": 200,
            "RESULT": {
                "average_RENT_GTN": avg_RENT_GTN,
                "average_RENT_FEE": avg_RENT_FEE
            }
        }
    else:
        raise HTTPException(status_code=400)

@app.get('/rent/get-year-upavg')
async def rent_getYearUpAvg(firstx: float, secondx: float, firsty: float, secondy: float):
    rent_collection = mydb['yearAreaUp']
    filter_criteria = {
        "x": {"$gte": firstx, "$lte": secondx},
        "y": {"$gte": firsty, "$lte": secondy},
    }
    
    rent_data = rent_collection.aggregate([
        {"$match": filter_criteria},
        {
            "$group": {
                "_id": None,
                "total_RENT_GTN": {"$sum": "$RENT_GTN"},
                "count": {"$sum": 1}
            }
        }
    ])
    rent_data = list(rent_data)
    if rent_data:
        total_RENT_GTN = rent_data[0]['total_RENT_GTN']
        count = rent_data[0]['count']
        avg_RENT_GTN = total_RENT_GTN / count
        return {
            "Status": 200,
            "RESULT": {
                "average_RENT_GTN": avg_RENT_GTN
            }
        }
    else:
        raise HTTPException(status_code=400)
    
@app.get('/rent/get-year-dwavg')
async def rent_getYearDwAvg(firstx: float, secondx: float, firsty: float, secondy: float):
    rent_collection = mydb['yearAreaDw']
    filter_criteria = {
        "x": {"$gte": firstx, "$lte": secondx},
        "y": {"$gte": firsty, "$lte": secondy},
    }
    
    rent_data = rent_collection.aggregate([
        {"$match": filter_criteria},
        {
            "$group": {
                "_id": None,
                "total_RENT_GTN": {"$sum": "$RENT_GTN"},
                "count": {"$sum": 1}
            }
        }
    ])
    rent_data = list(rent_data)
    if rent_data:
        total_RENT_GTN = rent_data[0]['total_RENT_GTN']
        count = rent_data[0]['count']
        avg_RENT_GTN = total_RENT_GTN / count
        return {
            "Status": 200,
            "RESULT": {
                "average_RENT_GTN": avg_RENT_GTN
            }
        }
    else:
        raise HTTPException(status_code=400)

# @app(/rent/less-ten-rank)
# async def rentLessTenRank(month, year):

# @app(/rent/more-ten-rank)
# async def rentMessTenRank(month, year):

# @app(/rent/get-rank)
# async def getRank():
#   await renLessTen(month, year)
#   await renMoreTen(month, year)
#   def rank_values(values):
    # # 값들과 해당 값의 순위를 튜플로 묶습니다.
    # ranked_values = sorted(((value, i) for i, value in enumerate(values, 1)), reverse=True)
    
    # # 정렬된 값을 기반으로 순위를 매깁니다.
    # ranks = [rank for value, rank in ranked_values]
    
    # return ranks

    # # 주어진 값들
    # values = [7, 3, 10, 5, 2]

    # # 값들의 순위 계산
    # ranks = rank_values(values)

    # # 결과 출력
    # print("Values:", values)
    # print("Ranked Values:", sorted(values, reverse=True))  # 값들 정렬하여 출력
    # print("Ranks:", ranks  

@app.post('/get-traffic-time')
async def getTrafficTime(request: Request):
    datas = await request.json()
    oftenPlace = datas.get('oftenPlace')
    wantPlace = datas.get('wantPlace')

    often_coordinates = search_address(oftenPlace)
    if not often_coordinates:
        print("ERROR : 자주 가는 곳 데이터가 없음")
        return {'success': False}
    often_x, often_y = often_coordinates

    for place in wantPlace:
        want_coordinates = search_address(place)
        if not want_coordinates:
            print("ERROR : 살고 싶은 곳 데이터가 없음")
            continue
        want_x, want_y = want_coordinates
        print(getTime(often_x, often_y, want_x, want_y))
        res = getTime(often_x, often_y, want_x, want_y)
    return res

@app.post('/rent/get-avg')
async def rent_getAvg(request: Request):
    data = await request.json()
    print(data)
    wantPlace = data.get('wantPlace')
    
    for place in wantPlace:
        coordinates = search_address(place)
        if coordinates:
            x, y = coordinates
        bounds = getXYBound(x, y)

        firstx = bounds["firstx"]
        firsty = bounds["firsty"]
        secondx = bounds["secondx"]
        secondy = bounds["secondy"]
        
        result1 = await rent_getMonthUpAvg(firstx, secondx, firsty, secondy)
        result2 = await rent_getMonthDwAvg(firstx, secondx, firsty, secondy)
        result3 = await rent_getYearUpAvg(firstx, secondx, firsty, secondy)
        result4 = await rent_getYearDwAvg(firstx, secondx, firsty, secondy)
        
        print(result1, result2, result3, result4)
        return {"getMonthUpAvg":result1, "getMonthDwAvg":result2, "getYearUpAvg":result3, "getYearDwAvg":result4}