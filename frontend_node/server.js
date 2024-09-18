const express = require('express');
const WebSocket = require('ws');
const io = require('socket.io-client');
const http = require('http');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });
const fs = require('fs');

// Connect to Python WebSocket server
const pythonWs = io('ws://127.0.0.1:5050');

pythonWs.on('connect', () => {
    console.log('Connected to Python server');
});

pythonWs.on('message', (data) => {
    console.log('Received message:', data);
});

pythonWs.on('error', (error) => {
    console.error('Error:', error);
});

wss.on('connection', function connection(ws) {
    ws.on('message', function incoming(message) {
        console.log('Received audio chunk from frontend:', message);
        // Forward the message (audio chunk) to the Python backend for processing
        if (pythonWs.connected) {
            pythonWs.emit('audio_chunk', message);
        } else {
            console.log('Python WebSocket not connected.');
        }
    }, { binary: true });

    ws.on('open', function open() {
        console.log('Frontend connected to Node.js WebSocket server');
    });

    ws.send('Node.js WebSocket server connected');
});

app.use(express.static('public'));

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
