import traceback

from .. import worker
from .. import profiler


class BaseExecutor:
    def __init__(
        self,
        work_method,
        update_current_task,
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
        self.work_method = work_method
        self.update_current_task = update_current_task
        self.on_success = on_success
        self.on_timeout = on_timeout
        self.on_failure = on_failure
        self.on_requeue = on_requeue
        self.on_retry = on_retry
        self.on_max_retries = on_max_retries
        self.report_complete = report_complete
        self.profiling_handler = profiling_handler
        self.worker_config = worker_config

    def begin_working(
        self,
    ):
        pass

    def end_working(
        self,
    ):
        pass

    def pre_work(
        self,
        task,
    ):
        pass

    def post_work(
        self,
    ):
        pass

    def execute_task(
        self,
        task,
    ):
        try:
            self.pre_work(
                task=task,
            )

            if self.worker_config['profiler']['enabled']:
                work_profiler = profiler.profiler.Profiler()
                work_profiler.start()

            returned_value = self.work_method(
                *task['args'],
                **task['kwargs'],
            )

            if self.worker_config['profiler']['enabled']:
                work_profiler.stop()

                self.profiling_handler(
                    profiling_data_generator=work_profiler.profiling_result(
                        num_of_slowest_methods=self.worker_config['profiler']['num_of_slowest_methods_to_log'],
                    ),
                    args=task['args'],
                    kwargs=task['kwargs'],
                )

            self.post_work()

            self.on_success(
                task=task,
                returned_value=returned_value,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            status = 'success'
        except (
            worker.WorkerSoftTimedout,
            worker.WorkerHardTimedout,
        ) as exception:
            exception_traceback = traceback.format_exc()
            self.on_timeout(
                task=task,
                exception=exception,
                exception_traceback=exception_traceback,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            status = 'timeout'
        except worker.WorkerRetry as exception:
            exception_traceback = traceback.format_exc()

            if self.worker_config['max_retries'] <= task['run_count']:
                self.on_max_retries(
                    task=task,
                    exception=exception,
                    exception_traceback=exception_traceback,
                    args=task['args'],
                    kwargs=task['kwargs'],
                )

                status = 'max_retries'
            else:
                self.on_retry(
                    task=task,
                    exception=exception,
                    exception_traceback=exception_traceback,
                    args=task['args'],
                    kwargs=task['kwargs'],
                )

                status = 'retry'
        except worker.WorkerRequeue as exception:
            exception_traceback = traceback.format_exc()

            self.on_requeue(
                task=task,
                exception=exception,
                exception_traceback=exception_traceback,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            status = 'requeue'
        except Exception as exception:
            exception_traceback = traceback.format_exc()
            self.on_failure(
                task=task,
                exception=exception,
                exception_traceback=exception_traceback,
                args=task['args'],
                kwargs=task['kwargs'],
            )

            status = 'failure'
        finally:
            self.post_work()

            if status not in [
                'retry',
                'requeue',
            ]:
                self.report_complete(
                    task=task,
                )

            return status
