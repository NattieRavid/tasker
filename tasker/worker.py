import datetime
import os
import signal
import logging
import traceback
import socket
import random
import time

from . import connector
from . import devices
from . import encoder
from . import logger
from . import monitor
from . import queue


class WorkerException(Exception):
    pass


class WorkerMaxRetriesException(WorkerException):
    pass


class WorkerRetryException(WorkerException):
    pass


class Worker:
    '''
    '''
    name = 'worker_name'

    compressor = 'zlib'
    serializer = 'msgpack'
    monitoring = {
        'host_name': socket.gethostname(),
        'stats_server': {
            'host': '',
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
    soft_timeout = 30.0
    hard_timeout = 35.0
    global_timeout = 0.0
    max_tasks_per_run = 10
    max_retries = 3
    tasks_per_transaction = 10
    report_completion = False
    heartbeat_interval = 10.0

    def __init__(self, abstract=False):
        self.logger = logger.logger.Logger(
            logger_name=self.name,
        )

        if abstract is True:
            return

        queue_connector_obj = connector.__connectors__[self.connector['type']]
        queue_connector = queue_connector_obj(**self.connector['params'])
        self.task_queue = queue.regular.Queue(
            queue_name=self.name,
            connector=queue_connector,
            encoder=encoder.encoder.Encoder(
                compressor_name=self.compressor,
                serializer_name=self.serializer,
            ),
        )

    def push_task(self, task):
        '''
        '''
        try:
            self.task_queue.enqueue(
                value=task,
            )

            return True
        except Exception as exception:
            self.logger.error(
                msg='could not push task: {exception}'.format(
                    exception=exception,
                )
            )

            return False

    def push_tasks(self, tasks):
        '''
        '''
        try:
            self.task_queue.enqueue_bulk(
                values=tasks,
            )

            return True
        except Exception as exception:
            self.logger.error(
                msg='could not push tasks: {exception}'.format(
                    exception=exception,
                )
            )

            return False

    def pull_task(self):
        '''
        '''
        try:
            task = self.task_queue.dequeue(
                timeout=0,
            )

            return task
        except Exception as exception:
            self.logger.error(
                msg='could not pull task: {exception}'.format(
                    exception=exception,
                )
            )

            return {}

    def pull_tasks(self, count):
        '''
        '''
        try:
            tasks = self.task_queue.dequeue_bulk(
                count=count,
            )

            return tasks
        except Exception as exception:
            self.logger.error(
                msg='could not pull tasks: {exception}'.format(
                    exception=exception,
                )
            )

            return []

    def purge_tasks(self):
        '''
        '''
        try:
            self.task_queue.flush()
        except Exception as exception:
            self.logger.error(
                msg='could not purge tasks: {exception}'.format(
                    exception=exception,
                )
            )

    def number_of_enqueued_tasks(self):
        '''
        '''
        try:
            number_of_enqueued_tasks = self.task_queue.len()

            return number_of_enqueued_tasks
        except Exception as exception:
            self.logger.error(
                msg='could not get len of queue: {exception}'.format(
                    exception=exception,
                )
            )

    def craft_task(self, *args, **kwargs):
        '''
        '''
        if self.report_completion:
            completion_key = self.create_completion_key()
        else:
            completion_key = None

        task = {
            'date': datetime.datetime.utcnow().timestamp(),
            'args': args,
            'kwargs': kwargs,
            'run_count': 0,
            'completion_key': completion_key,
        }

        return task

    def create_completion_key(self):
        '''
        '''
        added = False

        while not added:
            completion_key = random.randint(0, 9999999999999)
            added = self.task_queue.add_result(
                value=completion_key,
            )

        return completion_key

    def report_complete(self, task):
        '''
        '''
        completion_key = task['completion_key']

        if completion_key:
            removed = self.task_queue.remove_result(
                value=completion_key,
            )

            return removed
        else:
            return True

    def wait_task_finished(self, task, timeout=0):
        '''
        '''
        completion_key = task['completion_key']
        elapsed_time = timeout

        if not completion_key:
            return

        has_result = self.task_queue.has_result(
            value=completion_key,
        )
        while has_result:
            if timeout and elapsed_time <= 0:
                return

            has_result = self.task_queue.has_result(
                value=completion_key,
            )

            time.sleep(0.2)
            elapsed_time -= 0.2

    def apply_async_one(self, *args, **kwargs):
        '''
        '''
        task = self.craft_task(*args, **kwargs)

        self.push_task(
            task=task,
        )

        return task

    def apply_async_many(self, tasks):
        '''
        '''
        self.push_tasks(
            tasks=tasks,
        )

    def get_next_tasks(self, tasks_left):
        '''
        '''
        if self.tasks_per_transaction == 1:
            while True:
                task = self.pull_task()

                if task:
                    return [task]

        if tasks_left > self.tasks_per_transaction:
            tasks = self.pull_tasks(
                count=self.tasks_per_transaction,
            )
        else:
            tasks = self.pull_tasks(
                count=tasks_left,
            )

        if tasks:
            return tasks

        while True:
            task = self.pull_task()

            if task:
                return [task]

    def sigabrt_handler(self, signal_num, frame):
        raise TimeoutError()

    def sigint_handler(self, signal_num, frame):
        '''
        '''
        try:
            self.tasks_to_finish.remove(self.current_task)

            self._on_timeout(
                exception=TimeoutError('hard timeout'),
                args=self.current_task['args'],
                kwargs=self.current_task['kwargs'],
            )
        except:
            pass

        self.end_working()

        os.kill(os.getpid(), signal.SIGTERM)

    def begin_working(self):
        '''
        '''
        self.monitor_client = None
        self.heartbeater = None

        self.run_forever = False
        if self.max_tasks_per_run == 0:
            self.run_forever = True

        self.tasks_to_finish = []
        self.current_task = None
        self.tasks_left = 0

        if self.monitoring:
            self.monitor_client = monitor.client.StatisticsClient(
                stats_server=self.monitoring['stats_server'],
                host_name=self.monitoring['host_name'],
                worker_name=self.name,
            )
            self.heartbeater = devices.heartbeater.Heartbeater(
                monitor_client=self.monitor_client,
                interval=self.heartbeat_interval,
            )
            self.heartbeater.start()

        self.killer = devices.killer.Killer(
            soft_timeout=self.soft_timeout,
            soft_timeout_signal=signal.SIGABRT,
            hard_timeout=self.hard_timeout,
            hard_timeout_signal=signal.SIGINT,
        )
        signal.signal(signal.SIGABRT, self.sigabrt_handler)
        signal.signal(signal.SIGINT, self.sigint_handler)

        self.init()

        self.killer.create()

    def end_working(self):
        '''
        '''
        if self.tasks_to_finish:
            try:
                self.push_tasks(self.tasks_to_finish)
            except:
                pass

        logging.shutdown()

        if self.heartbeater:
            self.heartbeater.stop()

    def work_loop(self):
        '''
        '''
        try:
            self.begin_working()

            self.tasks_left = self.max_tasks_per_run
            while self.tasks_left > 0 or self.run_forever is True:
                tasks = self.get_next_tasks(
                    tasks_left=self.tasks_left,
                )
                if self.monitoring:
                    self.monitor_client.increment_process(
                        value=len(tasks),
                    )

                self.tasks_to_finish = tasks.copy()
                for task in tasks:
                    self.current_task = task
                    task_execution_result = self.execute_task(
                        task=task,
                    )
                    self.tasks_to_finish.remove(task)

                    if task_execution_result != 'retry':
                        self.report_complete(
                            task=task,
                        )

                    if not self.run_forever:
                        self.tasks_left -= 1
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self.logger.log_task_failure(
                failure_reason='Task Execution Exception',
                task_name=self.name,
                args=self.current_task['args'],
                kwargs=self.current_task['kwargs'],
                exception=exception,
                exception_traceback=exception_traceback,
            )
        finally:
            self.end_working()

    def execute_task(self, task):
        '''
        '''
        try:
            self.killer.reset()
            self.killer.start()

            returned_value = self.work(
                *task['args'],
                **task['kwargs']
            )

            self.killer.stop()

            self._on_success(
                returned_value=returned_value,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            return 'success'
        except TimeoutError as exception:
            exception_traceback = traceback.format_exc()
            self._on_timeout(
                exception=exception,
                exception_traceback=exception_traceback,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            return 'timeout'
        except WorkerRetryException as exception:
            self._on_retry(
                args=task['args'],
                kwargs=task['kwargs'],
            )

            return 'retry'
        except WorkerMaxRetriesException as exception:
            exception_traceback = traceback.format_exc()
            self._on_max_retries(
                exception=exception,
                exception_traceback=exception_traceback,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            return 'max_retries'
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self._on_failure(
                exception=exception,
                exception_traceback=exception_traceback,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            return 'exception'
        finally:
            self.killer.stop()

    def retry(self):
        '''
        '''
        if self.max_retries <= self.current_task['run_count']:
            raise WorkerMaxRetriesException(
                'max retries of: {max_retries}, exceeded'.format(
                    max_retries=self.max_retries,
                )
            )

        task = self.current_task
        task['run_count'] += 1

        self.push_task(
            task=task,
        )

        raise WorkerRetryException

    def _on_success(self, returned_value, args, kwargs):
        '''
        '''
        if self.monitoring:
            self.monitor_client.increment_success()

        self.logger.log_task_success(
            task_name=self.name,
            args=args,
            kwargs=kwargs,
            returned_value=returned_value,
        )

        try:
            self.on_success(
                returned_value=returned_value,
                args=args,
                kwargs=kwargs,
            )
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self.logger.log_task_failure(
                failure_reason='Exception during on_success',
                task_name=self.name,
                args=args,
                kwargs=kwargs,
                exception=exception,
                exception_traceback=exception_traceback,
            )

    def _on_failure(self, exception, exception_traceback, args, kwargs):
        '''
        '''
        if self.monitoring:
            self.monitor_client.increment_failure()

        self.logger.log_task_failure(
            failure_reason='Failue',
            task_name=self.name,
            args=args,
            kwargs=kwargs,
            exception=exception,
            exception_traceback=exception_traceback,
        )

        try:
            self.on_failure(
                exception=exception,
                exception_traceback=exception_traceback,
                args=args,
                kwargs=kwargs,
            )
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self.logger.log_task_failure(
                failure_reason='Exception during on_failure',
                task_name=self.name,
                args=args,
                kwargs=kwargs,
                exception=exception,
                exception_traceback=exception_traceback,
            )

    def _on_retry(self, args, kwargs):
        '''
        '''
        if self.monitoring:
            self.monitor_client.increment_retry()

        self.logger.log_task_retry(
            task_name=self.name,
            args=args,
            kwargs=kwargs,
        )

        try:
            self.on_retry(
                args=args,
                kwargs=kwargs,
            )
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self.logger.log_task_failure(
                failure_reason='Exception during on_retry',
                task_name=self.name,
                args=args,
                kwargs=kwargs,
                exception=exception,
                exception_traceback=exception_traceback,
            )

    def _on_timeout(self, exception, exception_traceback, args, kwargs):
        '''
        '''
        if self.monitoring:
            self.monitor_client.increment_failure()

        self.logger.log_task_failure(
            failure_reason='Timeout',
            task_name=self.name,
            args=args,
            kwargs=kwargs,
            exception=exception,
            exception_traceback=exception_traceback,
        )

        try:
            self.on_timeout(
                exception=exception,
                exception_traceback=exception_traceback,
                args=args,
                kwargs=kwargs,
            )
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self.logger.log_task_failure(
                failure_reason='Exception during on_timeout',
                task_name=self.name,
                args=args,
                kwargs=kwargs,
                exception=exception,
                exception_traceback=exception_traceback,
            )

    def _on_max_retries(self, exception, exception_traceback, args, kwargs):
        '''
        '''
        if self.monitoring:
            self.monitor_client.increment_failure()

        self.logger.log_task_failure(
            failure_reason='Max Retries',
            task_name=self.name,
            args=args,
            kwargs=kwargs,
            exception=exception,
            exception_traceback=exception_traceback,
        )

        try:
            self.on_max_retries(
                exception=exception,
                exception_traceback=exception_traceback,
                args=args,
                kwargs=kwargs,
            )
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self.logger.log_task_failure(
                failure_reason='Exception during on_max_retries',
                task_name=self.name,
                args=args,
                kwargs=kwargs,
                exception=exception,
                exception_traceback=exception_traceback,
            )

    def init(self):
        '''
        '''
        pass

    def work(self):
        '''
        '''
        pass

    def on_success(self, returned_value, args, kwargs):
        '''
        '''
        pass

    def on_failure(self, exception, exception_traceback, args, kwargs):
        '''
        '''
        pass

    def on_retry(self, args, kwargs):
        '''
        '''
        pass

    def on_max_retries(self, exception, exception_traceback, args, kwargs):
        '''
        '''
        pass

    def on_timeout(self, exception, exception_traceback, args, kwargs):
        '''
        '''
        pass

    def __getstate__(self):
        '''
        '''
        state = {
            'name': self.name,
            'compressor': self.compressor,
            'serializer': self.serializer,
            'monitoring': self.monitoring,
            'connector': self.connector,
            'soft_timeout': self.soft_timeout,
            'hard_timeout': self.hard_timeout,
            'max_tasks_per_run': self.max_tasks_per_run,
            'max_retries': self.max_retries,
            'tasks_per_transaction': self.tasks_per_transaction,
            'report_completion': self.report_completion,
            'heartbeat_interval': self.heartbeat_interval,
        }

        return state

    def __setstate__(self, value):
        '''
        '''
        self.name = value['name']
        self.compressor = value['compressor']
        self.serializer = value['serializer']
        self.monitoring = value['monitoring']
        self.connector = value['connector']
        self.soft_timeout = value['soft_timeout']
        self.hard_timeout = value['hard_timeout']
        self.max_tasks_per_run = value['max_tasks_per_run']
        self.max_retries = value['max_retries']
        self.tasks_per_transaction = value['tasks_per_transaction']
        self.report_completion = value['report_completion']
        self.heartbeat_interval = value['heartbeat_interval']

        self.__init__(
            abstract=False,
        )
