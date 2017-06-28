import tasker
import socket


class Worker(tasker.worker.Worker):
    name = 'test_worker'
    config = {
        'encoder': {
            'compressor': 'dummy',
            'serializer': 'pickle',
        },
        'monitoring': {
            'host_name': socket.gethostname(),
            'stats_server': {
                'host': 'localhost',
                'port': 9999,
            }
        },
        'connector': {
            'type': 'redis',
            'params': {
                'host': 'localhost',
                'port': 6380,
                'password': 'e082ebf6c7fff3997c4bb1cb64d6bdecd0351fa270402d98d35acceef07c6b97',
                'database': 0,
            },
        },
        'timeouts': {
            'soft_timeout': 3.0,
            'hard_timeout': 35.0,
            'critical_timeout': 0.0,
            'global_timeout': 0.0,
        },
        'limits': {
            'memory': 0,
        },
        'executor': {
            'type': 'serial',
            'config': {},
        },
        'max_tasks_per_run': 25000,
        'tasks_per_transaction': 1000,
        'max_retries': 3,
        'report_completion': False,
        'heartbeat_interval': 10.0,
    }


def main():
    supervisor = tasker.supervisor.Supervisor(
        worker_class=Worker,
        concurrent_workers=2,
    )
    supervisor.start()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        print('killed')
