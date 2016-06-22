var dgram = require('dgram');
var express = require('express');
var http = require('http');
var socket_io = require('socket.io');


var udp_server_port = 33333;
var udp_server_host = '0.0.0.0';
var udp_server = dgram.createSocket('udp4');

var web_server_port = 8000;
var web_server = express();

var websockets_server_port = 8001;
var websockets_http_server = http.createServer();
var websockets_server = socket_io(websockets_http_server);


websockets_server.on(
    'connection',
    function (socket) {
        socket.on(
            'event',
            function (data) {

            }
        );
        socket.on(
            'disconnect',
            function () {

            }
        );
    }
);

udp_server.on(
    'listening',
    function () {
    }
);

udp_server.on(
    'message',
    function (message, remote) {
    }
);

web_server.use(
    express.static('public')
);

web_server.listen(
    web_server_port,
    function () {
    }
);
udp_server.bind(udp_server_port, udp_server_host);
websockets_server.listen(websockets_server_port);