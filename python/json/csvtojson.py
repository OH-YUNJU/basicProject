import csv
import json

# csv 파일 경로
csv_file_path = '/root/basicProject/python/json/rent.csv'

# csv 파일 읽어오기
with open(csv_file_path, 'rt', encoding='cp949') as f:
    reader = csv.reader(f)
    next(reader)  # 첫 줄 skip

    data = {}
    data['rent'] = []
    for line in reader:
        d = {
            'ACC_YEAR': line[0],  # 접수연도
            'SGG_CD': line[1],  # 자치구코드
            'SGG_NM': line[2],  # 자치구명
            'BJDONG_CD': line[3],  # 법정동코드
            'BJDONG_NM': line[4],  # 법정동명
            'LAND_GBN': line[5],  # 지번구분
            'LAND_GBN_NM': line[6],  # 지번구분명
            'BOBN': line[7],  # 본번
            'BUBN': line[8],  # 부번
            'FLR_NO': line[9],  # 층
            'CNTRCT_DE': line[10],  # 계약일
            'RENT_GBN': line[11],  # 전월세 구분
            'RENT_AREA': line[12],  # 임대면적(㎡)
            'RENT_GTN': line[13],  # 보증금(만원)
            'RENT_FEE': line[14],  # 임대료(만원)
            'BLDG_NM': line[15],  # 건물명
            'BUILD_YEAR': line[16],  # 건축년도
            'HOUSE_GBN_NM': line[17],  # 건물용도
            'CNTRCT_PRD': line[18],  # 계약기간
            'NEW_RON_SECD': line[19],  # 신규갱신여부
            'CNTRCT_UPDT_RQEST_AT': line[20],  # 계약갱신권사용여부
            'BEFORE_GRNTY_AMOUNT': line[21],  # 종전 보증금
            'BEFORE_MT_RENT_CHRGE': line[22]  # 종전 임대료
        }
        data['rent'].append(d)

# json string으로 변환
#json_string = json.dumps(data, ensure_ascii=False, indent=2)

# print(json_string)

file_path = '/root/basicProject/python/json/seoul_budongsan.json'

# 파일 쓰기
with open(file_path, 'wt', encoding='utf-8') as f:
    f.write(json.dumps(data, ensure_ascii=False, indent=4))