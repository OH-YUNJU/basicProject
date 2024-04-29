const express = require('express')
const bodyParser = require('body-parser')
const axios = require('axios');

const app = express()

app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: false }))
app.use(express.json())
app.use(express.urlencoded({ extended: true }))


const handleRequest = async (req, res) => {
    const { oftenPlace, wantPlace } = req.body;

    console.log('자주 가는 곳:', oftenPlace);
    console.log('원하는 곳:', wantPlace);

    try {
        const [trafficTimeResponse, avgRentResponse] = await Promise.all([
            axios.post('http://192.168.1.98:3000/rent/get-avg', {
                oftenPlace,
                wantPlace
            }),
            axios.post('http://192.168.1.98:3000/get-traffic-time', {
                oftenPlace,
                wantPlace,
            })
        ]);

        // 응답 처리
        console.log('교통 시간 응답:', trafficTimeResponse.data);
        console.log('평균 임대료 응답:', avgRentResponse.data);


    } catch (error) {
        console.error('Error:', error);
        res.status(400).json({ status: 400, error: 'Internal Server Error' });
    }
}
app.post('/api/get-place', handleRequest);

app.get('/select-less-ten', (req, res) => {

})

app.get('/select-more-ten', (req, res) => {

})

module.exports = app;