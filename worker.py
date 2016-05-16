import tasker
import time


class Worker(tasker.worker.Worker):
    name = 'test_worker'

    compressor = 'dummy'
    serializer = 'pickle'
    monitoring = {
        'host_name': '',
        'stats_server': {
            'host': '127.0.0.1',
            'port': 9999,
        }
    }
    connector = {
        'type': 'redis',
        'params': {
            'host': 'localhost',
            'port': 6379,
            'database': 0,
        },
    }
    soft_timeout = 3.0
    hard_timeout = 35.0
    global_timeout = 0.0
    max_tasks_per_run = 25000
    tasks_per_transaction = 1000
    max_retries = 3
    report_completion = False
    heartbeat_interval = 10.0

    def init(self):
        self.a = 0

    def work(self, num):
        self.a += num

        if num == 4:
            self.logger.error('start')
            self.logger.error(time.time())
        if num == 6:
            self.logger.error('end')
            self.logger.error(time.time())z


def main():
    supervisor = tasker.supervisor.Supervisor(
        worker_class=Worker,
        concurrent_workers=4,
    )
    supervisor.start()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        print('killed')
