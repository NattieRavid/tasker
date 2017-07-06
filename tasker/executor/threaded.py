import ctypes
import threading
import concurrent.futures

from . import executor
from .. import worker


class ThreadedExecutor(
    executor.BaseExecutor,
):
    def __init__(
        self,
        work_method,
        on_success,
        on_timeout,
        on_failure,
        on_requeue,
        on_retry,
        on_max_retries,
        report_complete,
        profiling_handler,
        worker_config,
    ):
        super().__init__(
            work_method=work_method,
            on_success=on_success,
            on_timeout=on_timeout,
            on_failure=on_failure,
            on_requeue=on_requeue,
            on_retry=on_retry,
            on_max_retries=on_max_retries,
            report_complete=report_complete,
            profiling_handler=profiling_handler,
            worker_config=worker_config,
        )
        self.concurrency = self.worker_config['executor']['concurrency']

    def execute_tasks(
        self,
        tasks,
    ):
        future_to_task = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.concurrency,
        ) as executor:
            for task in tasks:
                future = executor.submit(self.execute_task, task)
                future_to_task[future] = task

        for future in concurrent.futures.as_completed(future_to_task):
            pass

    def pre_work(
        self,
    ):
        self.timeout_timer = threading.Timer(
            interval=self.worker_config['timeouts']['soft_timeout'],
            function=ctypes.pythonapi.PyThreadState_SetAsyncExc,
            args=(
                ctypes.c_long(threading.get_ident()),
                ctypes.py_object(worker.WorkerSoftTimedout),
            )
        )
        self.timeout_timer.start()

    def post_work(
        self,
    ):
        self.timeout_timer.cancel()
