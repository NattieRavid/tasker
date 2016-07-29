import unittest
import time
import os
import signal

from .. import devices


class DummyMonitorClient:
    def __init__(self):
        self.counter = 0

    def increment_heartbeat(self):
        self.counter += 1


class DevicesTestCase(unittest.TestCase):
    def setUp(self):
        self.monitor_client = DummyMonitorClient()
        self.heartbeater = devices.heartbeater.Heartbeater(
            monitor_client=self.monitor_client,
            interval=1.0,
        )

        self.local_killer = devices.killer.LocalKiller(
            soft_timeout=1.0,
            soft_timeout_signal=signal.SIGINT,
            hard_timeout=3.0,
            hard_timeout_signal=signal.SIGABRT,
        )
        self.remote_killer = devices.killer.RemoteKiller(
            soft_timeout=1.0,
            soft_timeout_signal=signal.SIGINT,
            hard_timeout=3.0,
            hard_timeout_signal=signal.SIGABRT,
        )
        signal.signal(signal.SIGABRT, self.sigabrt_handler)
        signal.signal(signal.SIGINT, self.sigint_handler)

        self.sigint_fired = False
        self.sigabrt_fired = False

    def sigabrt_handler(self, signal_num, frame):
        self.sigabrt_fired = True

    def sigint_handler(self, signal_num, frame):
        '''
        '''
        self.sigint_fired = True

    def test_heartbeater(self):
        self.heartbeater.start()
        self.assertEqual(self.monitor_client.counter, 0)
        time.sleep(1.2)
        self.assertEqual(self.monitor_client.counter, 1)
        time.sleep(1.2)
        self.assertEqual(self.monitor_client.counter, 2)
        self.heartbeater.stop()
        time.sleep(1.2)
        self.assertEqual(self.monitor_client.counter, 2)

    def test_local_killer(self):
        self.local_killer.start()
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertTrue(self.sigint_fired)
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertTrue(self.sigint_fired)
        time.sleep(1.2)
        self.assertTrue(self.sigabrt_fired)
        self.assertTrue(self.sigint_fired)
        self.local_killer.stop()

        self.sigint_fired = False
        self.sigabrt_fired = False
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)

        self.local_killer.reset()
        self.local_killer.start()
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.local_killer.reset()
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.local_killer.reset()
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.local_killer.reset()
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.local_killer.reset()
        self.local_killer.stop()
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)

    def test_remote_killer(self):
        self.remote_killer.start()
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertTrue(self.sigint_fired)
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertTrue(self.sigint_fired)
        time.sleep(1.2)
        self.assertTrue(self.sigabrt_fired)
        self.assertTrue(self.sigint_fired)
        self.remote_killer.stop()

        self.sigint_fired = False
        self.sigabrt_fired = False
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        time.sleep(1.2)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)

        self.remote_killer.reset()
        self.remote_killer.start()
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.remote_killer.reset()
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.remote_killer.reset()
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.remote_killer.reset()
        time.sleep(0.5)
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
        self.remote_killer.reset()
        self.remote_killer.stop()
        self.assertFalse(self.sigabrt_fired)
        self.assertFalse(self.sigint_fired)
