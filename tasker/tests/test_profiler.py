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
    def printing_func_to_profile():
        print('This is a worker profiling test')

    @staticmethod
    def http_request_func_to_profile(
        time_to_wait,
    ):
        time.sleep(time_to_wait)

        requests.get('https://www.google.com')

    def test_profiler_regex(
        self,
    ):
        methods_profiling = []

        expected_results = [
            {
                'method': 'printing_func_to_profile',
                'library': None,
                'line_number': '16',
            },
            {
                'method': 'builtins.print',
                'library': None,
                'line_number': None,
            },
        ]
        expected_methods = [
            x['method']
            for x in expected_results
        ]

        self.profiler.start()

        self.printing_func_to_profile()

        self.profiler.stop()

        for method_profile in self.profiler.profiler.getstats():
            method_properties = self.profiler.properties_regex.search(str(method_profile.code))
            method = method_properties.group('method')
            if method not in expected_methods:
                continue

            method_properties_dict = {
                'method': method,
                'library': method_properties.group('lib'),
                'line_number': method_properties.group('line_number'),
            }
            filename = method_properties.group('filename')

            if method_properties_dict['line_number']:
                self.assertTrue(
                    str.endswith(filename, '.py'),
                    msg='profiling does not record the filename',
                )
            else:
                self.assertIsNone(
                    filename,
                    msg='profiling method filename is invalid',
                )

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
        http_request_func_to_profile_time_to_wait = 3

        self.profiler.start()

        self.http_request_func_to_profile(
            time_to_wait=http_request_func_to_profile_time_to_wait,
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
            if 'http_request_func_to_profile' in method_profile['method']:
                http_request_func_to_profile_method_profile = method_profile
                break

        http_request_func_to_profile_method_profile.pop('task_profiling_id')
        method_time_consumed = http_request_func_to_profile_method_profile.pop('time_consumed')
        filename = http_request_func_to_profile_method_profile.pop('filename')

        expected_method_profile = {
            'method': 'http_request_func_to_profile',
            'library': 'None',
            'line_number': '20',
        }

        self.assertDictEqual(
            http_request_func_to_profile_method_profile,
            expected_method_profile,
            msg='Dicts are not equal',
        )

        self.assertGreater(
            method_time_consumed,
            http_request_func_to_profile_time_to_wait,
            msg='time consumed is incorrect',
        )

        self.assertEqual(
            type(filename),
            str,
            msg='profiling method filename is invalid',
        )
