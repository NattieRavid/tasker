var TaskerDashboard = angular.module(
    'TaskerDashboard',
    [
        'ngWebSocket',
    ]
);


TaskerDashboard.controller(
    'DashboardController',
    [
        '$scope',
        '$websocket',
        '$location',
        '$interval',
        function DashboardController($scope, $websocket, $location, $interval) {
            $scope.statistics = {
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
                }
            };
            var host = $location.host();
            var websocket = io('http://localhost:8000');

            websocket.on(
                'statistics',
                function(data) {
                    $scope.statistics = data;
                }
            );
            websocket.on(
                'queues',
                function(data) {
                    $scope.queues = data;
                    console.log(data);
                }
            );

            $interval(
                function() {
                    websocket.emit(
                        'statistics',
                        {}
                    );
                },
                1000
            );
            $interval(
                function() {
                    websocket.emit(
                        'queues',
                        {}
                    );
                },
                5000
            );
        }
    ]
);
