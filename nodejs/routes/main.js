const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const mysql = require('mysql2');

const app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const fs = require('fs');


try {
    const secretData = fs.readFileSync('../python/secret.json', 'utf8');
    const secretConfig = JSON.parse(secretData);

    // MySQL 연결 설정
    var connection = mysql.createConnection({
        host: secretConfig.Mysql_Hostname,
        user: secretConfig.Mysql_Username,
        password: secretConfig.Mysql_Password,
        database: secretConfig.Mysql_DBname
    });

    connection.connect((err) => {
        if (err) {
            console.error('MySQL 연결 오류:', err);
        } else {
            console.log('MySQL 연결 성공');
        }
    });
} catch (error) {
    console.error('파일 읽기/파싱 오류:', error);
}

/* ================================================================ */


const handleRequest = async (req, res) => {
    const { oftenPlace, wantPlace } = req.body;

    console.log('자주 가는 곳:', oftenPlace);
    console.log('원하는 곳:', wantPlace);

    const trafficTimeResponses = [];
    const avgRentResponses = [];
    const resultsArray = [];

    try {
        for (const place of wantPlace) {
            console.log(place);

            // 교통 시간 응답 가져오기
            const trafficTimeResponse = await axios.post('http://192.168.1.98:3000/get-traffic-time', {
                oftenPlace,
                wantPlace: place,
            });
            console.log('교통 시간 응답:', trafficTimeResponse.data);
            trafficTimeResponses.push(trafficTimeResponse.data);

            // 평균 임대료 응답 가져오기
            const avgRentResponse = await axios.post('http://192.168.1.98:3000/rent/get-avg', {
                wantPlace: place,
            });
            console.log('평균 임대료 응답:', avgRentResponse.data);
            avgRentResponses.push(avgRentResponse.data);
        }

        // 각 wantPlace에 대한 데이터를 순회하여 데이터베이스에 삽입 및 결과 수집
        for (let i = 0; i < wantPlace.length; i++) {
            const trafficTimeData = trafficTimeResponses[i];
            const avgRentData = avgRentResponses[i];
            console.log(trafficTimeData.min_total_time);
            console.log(avgRentData);

            const minTotalTime = trafficTimeData.min_total_time;
            const avgRentMonthUpFee = avgRentData.getMonthUpAvg.RESULT.average_RENT_FEE;
            const avgRentMonthDwFee = avgRentData.getMonthDwAvg.RESULT.average_RENT_FEE;
            const avgRentYearUpGTN = avgRentData.getYearUpAvg.RESULT.average_RENT_GTN;
            const avgRentYearDwGTN = avgRentData.getYearDwAvg.RESULT.average_RENT_GTN;

            const insertQuery = `
                INSERT INTO housing_data (oftenplace, wantplace, time, less_month_avg, more_month_avg, less_year_avg, more_year_avg)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            `;

            const values = [
                oftenPlace,
                wantPlace[i],
                minTotalTime,
                avgRentMonthDwFee,
                avgRentMonthUpFee,
                avgRentYearDwGTN,
                avgRentYearUpGTN,
            ];

            await new Promise((resolve, reject) => {
                connection.query(insertQuery, values, (err, results) => {
                    if (err) {
                        console.error('데이터 삽입 오류:', err);
                        resultsArray.push({ success: false, error: err });
                        reject(err);
                    } else {
                        console.log('데이터 삽입 성공:', results);
                        resultsArray.push({ success: true, result: results });
                        resolve(results);
                    }
                });
            });
        }

        res.status(200).json({ status: 200, results: resultsArray });

    } catch (error) {
        console.error('Error:', error);
        res.status(400).json({ status: 400, error: 'Internal Server Error' });
    }
};

app.post('/api/get-oftenplace', handleRequest);


// sql 다 지우는 함수도 만들기                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         

const mapRequestLess = async (req, res) => {
    const { oftenPlace, wantPlace } = req.body;
    for (const place of wantPlace) {
        const mapResponse = await axios.post('http://192.168.1.98:3000/get/less-map-marker', {
            oftenPlace,
            wantPlace: place,
        });
        console.log('지도 응답:', mapResponse.data);
    }
};
app.post('/api/show-map-less', mapRequestLess);

const mapRequestMore = async (req, res) => {
    const { oftenPlace, wantPlace } = req.body;
    for (const place of wantPlace) {
        const mapResponse = await axios.post('http://192.168.1.98:3000/get/more-map-marker', {
            oftenPlace,
            wantPlace: place,
        });
        console.log('지도 응답:', mapResponse.data);
    }
};
app.post('/api/show-map-more', mapRequestMore);

module.exports = app;
