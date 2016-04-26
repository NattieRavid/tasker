import tasker
import logging


class Task(tasker.task.Task):
    name = 'test_task'

    compressor = 'dummy'
    serializer = 'pickle'
    monitoring = {
        'host_name': '',
        'stats_server': {
            'host': '127.0.0.1',
            'port': 9999,
        }
    }
    timeout = 30.0
    max_tasks_per_run = 10000
    tasks_per_transaction = 1000
    max_retries = 3
    log_level = logging.ERROR

    def init(self):
        self.a = 0

    def work(self, num):
        self.a += num


def main():
    connector = tasker.connector.redis.Connector(
        host='localhost',
        port=6379,
        database=0,
    )
    worker = tasker.worker.Worker(
        task_class=Task,
        connector_obj=connector,
        concurrent_workers=4,
        autoscale=False,
    )
    worker.log_level = logging.ERROR
    worker.start()

if __name__ == '__main__':
    try:
        main()
    except:
        print('killed')
