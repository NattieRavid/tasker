var bluebird = require('bluebird');
var dgram = require('dgram');
var express = require('express');
var http = require('http');
var socket_io = require('socket.io');
var msgpack = require('msgpack-lite');
var redis = require('redis');

bluebird.promisifyAll(redis.RedisClient.prototype);
bluebird.promisifyAll(redis.Multi.prototype);


var redis_client = redis.createClient(
    {
        'host': '127.0.0.1',
        'port': 6380,
    }
);

var udp_server_port = 33333;
var udp_server_host = '0.0.0.0';
var udp_server = dgram.createSocket('udp4');

var web_server_port = 8000;
var web_server = express();

var websockets_http_server = http.Server(web_server);
var websockets_server = socket_io(websockets_http_server);


var Statistics = function () {
    this.statistics = {
        'counter': {
            'process': 0,
            'success': 0,
            'retry': 0,
            'failure': 0
        },
        'rate': {
            'process': 0,
            'success': 0,
            'retry': 0,
            'failure': 0,
        },
        'last_log': {
            'process': [0, 0, 0, 0, 0],
            'success': [0, 0, 0, 0, 0],
            'retry': [0, 0, 0, 0, 0],
            'failure': [0, 0, 0, 0, 0]
        }
    };

    this.update_rate = function (rate) {
        var total_count = 0;

        this.statistics.last_log[rate].unshift(this.statistics.counter[rate]);

        for (var i = 0; i < this.statistics.last_log[rate].length - 1; i++) {
            total_count += this.statistics.last_log[rate][i] - this.statistics.last_log[rate][i + 1];
        }
        this.statistics.last_log[rate].pop();

        if (total_count > 0) {
            this.statistics.rate[rate] = total_count / 5.0;
        } else {
            this.statistics.rate[rate] = 0;
        }
    }

    this.increase = function (type, amount) {
        var message_type = {
            0: 'process',
            1: 'success',
            2: 'failure',
            3: 'retry',
            4: 'heartbeat'
        };
        var message_type_value = message_type[type];

        this.statistics.counter[message_type_value] += amount;
    }
}

var statistics = new Statistics();
setInterval(
    function () {
        statistics.update_rate('process');
        statistics.update_rate('success');
        statistics.update_rate('retry');
        statistics.update_rate('failure');
    },
    1000
);

websockets_server.on(
    'connection',
    function (socket) {
        socket.on(
            'statistics',
            function (data) {
                socket.emit(
                    'statistics',
                    statistics.statistics
                );
            }
        );
        socket.on(
            'queues',
            function (data) {
                redis_client
                .multi()
                .keys('*')
                .execAsync()
                .then(
                    function(result) {
                        var queues_names = result[0];
                        var queues_len_promises = [];

                        for (var i = 0; i < queues_names.length; i++) {
                            var llen_promise = null;
                            var queue_name = queues_names[i];

                            if (queue_name.indexOf('.results') > -1) {
                                llen_promise = redis_client.scardAsync(
                                    queue_name
                                );
                            } else if (queue_name.indexOf(':') === -1) {
                                llen_promise = redis_client.llenAsync(
                                    queue_name
                                );
                            } else {
                                continue;
                            }

                            queues_len_promises.push(
                                new bluebird.Promise(
                                    function(resolve, reject) {
                                        return llen_promise.then(
                                            function(queue_name) {
                                                return function(length) {
                                                    return resolve(
                                                        {
                                                            'name': queue_name,
                                                            'length': length
                                                        }
                                                    );
                                                }
                                            }(queue_name)
                                        )
                                    }
                                )
                            );
                        }

                        return bluebird.all(queues_len_promises);
                    }
                )
                .then(
                    function(results) {
                        socket.emit('queues', results);
                    }
                );
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
        var message_struct = {
            HOSTNAME: 0,
            WORKER_NAME: 1,
            MESSAGE_TYPE: 2,
            MESSAGE_VALUE: 3,
            DATE: 4
        };

        unpacked_message = msgpack.decode(message);
        statistics.increase(
            unpacked_message[message_struct.MESSAGE_TYPE],
            unpacked_message[message_struct.MESSAGE_VALUE]
        );
    }
);

web_server.use(
    express.static('public')
);

websockets_http_server.listen(
    web_server_port,
    function () {
    }
);
udp_server.bind(udp_server_port, udp_server_host);
