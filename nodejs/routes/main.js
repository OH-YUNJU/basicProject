const express = require('express')
const bodyParser = require('body-parser')
const axios = require('axios');

const app = express()

app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: false }))
app.use(express.json())
app.use(express.urlencoded({ extended: true }))


async function handleRequest(req, res) {
    const { oftenPlace, wantPlace } = req.body;

    console.log('자주 가는 곳:', oftenPlace);
    console.log('원하는 곳:', wantPlace);

    try {
        // Python 서버로 요청 보내기
        const response = await axios.post('http://192.168.1.98:3000/get-traffic-time', {
            oftenPlace,
            wantPlace,
        });

        const trafficTime = response.data;

        res.json({ status: 200, trafficTime });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ status: 500, error: 'Internal Server Error' });
    }
}
app.post('/api/get-oftenplace', handleRequest);

app.get('/api/get-wantplace', (req, res) => {

})

app.get('/api/search-page', (req, res) => {

})

app.get('/select-less-ten', (req, res) => {

})

app.get('/select-more-ten', (req, res) => {

})

module.exports = app;