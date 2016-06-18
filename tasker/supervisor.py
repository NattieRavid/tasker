import sys
import threading
import multiprocessing
import multiprocessing.pool

from . import logger


class Supervisor:
    '''
    '''

    def __init__(self, worker_class, concurrent_workers):
        self.logger = logger.logger.Logger(
            logger_name='Supervisor',
        )

        self.worker_class = worker_class
        self.concurrent_workers = concurrent_workers

        self.task = self.worker_class(
            abstract=True,
        )

        self.workers_processes = []

        self.should_work_event = threading.Event()
        self.should_work_event.set()

    def worker_watchdog(self, function):
        '''
        '''
        while self.should_work_event.is_set():
            try:
                context = multiprocessing.get_context(
                    method='spawn',
                )
                heartbeat_pipe_parent, heartbeat_pipe_child = context.Pipe()
                process = context.Process(
                    target=function,
                    kwargs={
                        'supervisor_report_pipe': heartbeat_pipe_child,
                    },
                )
                process.start()
                self.workers_processes.append(process)

                run_time = 0.0
                time_to_heartbeat = self.task.soft_timeout + 5
                while process.is_alive():
                    if heartbeat_pipe_parent.poll(0):
                        time_to_heartbeat = self.task.soft_timeout + 5

                    if self.task.global_timeout != 0.0 and run_time > self.task.global_timeout:
                        raise TimeoutError('global timeout has reached')

                    if time_to_heartbeat == 0:
                        raise TimeoutError('task stopped respond to heartbeats')
                    else:
                        time_to_heartbeat -= 1

                    process.join(
                        timeout=1.0,
                    )
            except Exception as exception:
                self.logger.error(
                    'task execution raised an exception: {exception}'.format(
                        exception=exception,
                    )
                )
            finally:
                process.terminate()
                self.workers_processes.remove(process)

    def start(self):
        '''
        '''
        threads = []
        for i in range(self.concurrent_workers):
            thread = threading.Thread(
                target=self.worker_watchdog,
                kwargs={
                    'function': self.task.work_loop,
                },
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)

        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            pass
        except Exception as exception:
            print(exception)
        finally:
            self.should_work_event.clear()
            for worker_process in self.workers_processes:
                worker_process.terminate()
            sys.exit(0)

    def __getstate__(self):
        '''
        '''
        state = {
            'worker_class': self.worker_class,
            'concurrent_workers': self.concurrent_workers,
        }

        return state

    def __setstate__(self, value):
        '''
        '''
        self.__init__(
            worker_class=value['worker_class'],
            concurrent_workers=value['concurrent_workers'],
        )
