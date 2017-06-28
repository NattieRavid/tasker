import unittest
import time
import requests

from .. import profiler


class ProfilerTestCase(
    unittest.TestCase,
):
    def setUp(
        self,
    ):
        self.profiler = profiler.profiler.Profiler()

    @staticmethod
    def dummy_func_1():
        print('This is a worker profiling test')

    @staticmethod
    def dummy_func_2(
        time_to_wait,
    ):
        x = 4

        for i in range(5):
            print('Hey there!')

            x *= 8

        time.sleep(time_to_wait)

        requests.get('https://www.google.com')

    def test_profiler_regex(
        self,
    ):
        methods_profiling = []

        expected_results = [
            {
                'method': 'dummy_func_1',
                'filename': '/backend/worker/libs/tasker/tasker/tests/test_profiler.py',
                'library': None,
                'line_number': '16',
            },
            {
                'method': 'stop',
                'filename': '/backend/worker/libs/tasker/tasker/profiler/profiler.py',
                'library': None,
                'line_number': '31',
            },
            {
                'method': 'disable',
                'filename': None,
                'library': '_lsprof.Profiler',
                'line_number': None,
            },
            {
                'method': 'builtins.print',
                'filename': None,
                'library': None,
                'line_number': None,
            },
        ]

        self.profiler.start()

        self.dummy_func_1()

        self.profiler.stop()

        for method_profile in self.profiler.profiler.getstats():
            method_properties = self.profiler.properties_regex.search(str(method_profile.code))
            method_properties_dict = {
                'method': method_properties.group('method'),
                'filename': method_properties.group('filename'),
                'library': method_properties.group('lib'),
                'line_number': method_properties.group('line_number'),
            }
            methods_profiling.append(method_properties_dict)

        self.assertEqual(
            methods_profiling,
            expected_results,
            msg='profiling regex failed'
        )

    def test_profiling_result(
        self,
    ):
        methods_count = 5
        dummy_func_2_time_to_wait = 3

        self.profiler.start()

        self.dummy_func_2(
            time_to_wait=dummy_func_2_time_to_wait,
        )

        self.profiler.stop()

        num_of_profiled_methods = len(self.profiler.profiler.getstats())
        self.assertGreater(
            num_of_profiled_methods,
            methods_count,
            msg=f'profiler collected statistics count is lower than {num_of_profiled_methods}',
        )

        profiling_statistics = list(
            self.profiler.profiling_result(
                num_of_slowest_methods=methods_count,
            )
        )

        self.assertEqual(
            len(profiling_statistics),
            methods_count,
            msg='profiler collected statistics count is not equal to the specified count limit',
        )

        for method_profile in profiling_statistics:
            if 'dummy_func_2' in method_profile['method']:
                dummy_func_2_method_profile = method_profile
                break

        dummy_func_2_method_profile.pop('task_profiling_id')
        method_time_consumed = dummy_func_2_method_profile.pop('time_consumed')

        expected_method_profile = {
            'method': 'dummy_func_2',
            'filename': '/backend/worker/libs/tasker/tasker/tests/test_profiler.py',
            'library': 'None',
            'line_number': '20',
        }

        self.assertDictEqual(
            dummy_func_2_method_profile,
            expected_method_profile,
            msg='Dicts are not equal',
        )

        self.assertGreater(
            method_time_consumed,
            dummy_func_2_time_to_wait,
            msg='time consumed is incorrect',
        )
