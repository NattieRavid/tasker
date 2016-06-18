import unittest
import datetime
import time

from .. import worker
from .. import scheduler


class DummyTask(worker.Worker):
    name = 'dummy_test_task'


class SchedulerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.task = DummyTask()

        self.scheduler = scheduler.Scheduler()

    @classmethod
    def tearDownClass(self):
        self.scheduler.terminate()
        self.task.task_queue.flush()

    def test_run_now(self):
        queue = self.task.task_queue
        queue.flush()

        self.scheduler.start()

        self.assertEqual(
            first=queue.len(),
            second=0,
        )
        self.scheduler.run_now(
            task=self.task,
            args=[],
            kwargs={},
        )
        time.sleep(0.5)
        self.assertEqual(
            first=queue.len(),
            second=1,
        )

        self.scheduler.stop()
        self.scheduler.clear()

    def test_run_in(self):
        queue = self.task.task_queue
        queue.flush()

        self.scheduler.start()

        self.assertEqual(
            first=queue.len(),
            second=0,
        )
        self.scheduler.run_in(
            task=self.task,
            args=[],
            kwargs={},
            time_delta=datetime.timedelta(
                seconds=1,
            ),
        )
        for i in range(8):
            self.assertEqual(
                first=queue.len(),
                second=0,
            )
            time.sleep(0.1)

        time.sleep(0.3)
        self.assertEqual(
            first=queue.len(),
            second=1,
        )

        self.scheduler.stop()
        self.scheduler.clear()

    def test_run_at(self):
        queue = self.task.task_queue
        queue.flush()

        self.scheduler.start()

        self.assertEqual(
            first=queue.len(),
            second=0,
        )
        self.scheduler.run_at(
            task=self.task,
            args=[],
            kwargs={},
            date_to_run_at=datetime.datetime.utcnow() + datetime.timedelta(
                seconds=1,
            ),
        )
        for i in range(8):
            self.assertEqual(
                first=queue.len(),
                second=0,
            )
            time.sleep(0.1)

        time.sleep(0.3)
        self.assertEqual(
            first=queue.len(),
            second=1,
        )

        self.scheduler.stop()
        self.scheduler.clear()

    def test_run_every(self):
        queue = self.task.task_queue
        queue.flush()

        self.scheduler.start()

        self.assertEqual(
            first=queue.len(),
            second=0,
        )
        self.scheduler.run_every(
            task=self.task,
            args=[],
            kwargs={},
            time_delta=datetime.timedelta(
                seconds=1,
            ),
        )

        for i in range(3):
            for j in range(8):
                self.assertEqual(
                    first=queue.len(),
                    second=i,
                )
                time.sleep(0.1)

            time.sleep(0.3)
            self.assertEqual(
                first=queue.len(),
                second=i + 1,
            )
        else:
            self.scheduler.stop()
            time.sleep(1.2)
            self.assertEqual(
                first=queue.len(),
                second=i + 1,
            )

        self.scheduler.clear()
