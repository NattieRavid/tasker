import uuid
import collections
import re
import cProfile


class Profiler:
    profiler = cProfile.Profile()
    properties_regex = re.compile(
        pattern=r'''
            ^<
            (code\sobject|(built-in\s)?method)
            \s[<\']?
            (?P<method>[\w\.]+)
            (.*file\s"
                (?P<filename>[\/\w\. \-]+)",\sline\s
                (?P<line_number>\d+)
                |\'\sof\s\'
                (?P<lib>[\w\.]+)
            )?
        ''',
        flags=re.IGNORECASE | re.VERBOSE,
    )

    def start(
        self,
    ):
        self.profiler.clear()
        self.profiler.enable()

    def stop(
        self,
    ):
        self.profiler.disable()

    def profiling_result(
        self,
        num_of_slowest_methods,
    ):
        method_profiles = []
        task_profiling_id = str(uuid.uuid4())
        methods_profiles = collections.defaultdict(int)

        for method_profile in self.profiler.getstats():
            methods_profiles[str(method_profile.code)] += method_profile.totaltime

        sorted_methods_by_totaltime = sorted(
            methods_profiles.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        slowest_methods = dict(
            sorted_methods_by_totaltime[:num_of_slowest_methods],
        )
        for profiling_output, time_length in slowest_methods.items():
            results = self.properties_regex.search(
                string=profiling_output,
            )
            if not results:
                continue

            method_profile = {
                'method': results.group('method'),
                'filename': results.group('filename') or 'external_library',
                'library': results.group('lib') or 'None',
                'line_number': results.group('line_number') or '',
                'time_consumed': time_length,
                'task_profiling_id': task_profiling_id,
            }

            method_profiles.append(method_profile)

        return method_profiles
