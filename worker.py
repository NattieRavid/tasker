import tasker
import logging
import time


class Task(tasker.task.Task):
    name = 'test_task'

    compression = 'none'
    timeout = 30.0
    max_tasks_per_run = 10000
    tasks_per_transaction = 10000
    max_retries = 3
    log_level = logging.INFO

    def init(self):
        self.a = 0

    def work(self, num):
        self.a += num


def main():
    connector = tasker.connectors.redis.Connector(
        host='localhost',
        port=6379,
        database=0,
    )

    task_queue = tasker.queue.Queue(
        connector=connector,
        queue_name='test_task',
        compressor='none',
        serializer='msgpack',
    )

    # task = Task(
    #     task_queue=task_queue,
    # )

    worker = tasker.worker.Worker(Task, task_queue, 4, False)
    worker.log_level = logging.DEBUG
    worker.start()

if __name__ == '__main__':
    try:
        main()
    except:
        print('killed')
