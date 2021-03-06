import setuptools


setuptools.setup(
    name='tasker',
    version='0.3.0',
    author='gal@intsights.com',
    author_email='gal@intsights.com',
    description=('A fast, simple, task distribution library'),
    zip_safe=True,
    install_requires=[
        'redis',
        'hiredis',
        'msgpack-python',
        'psutil',
        'aiohttp',
        'aioredis',
        'uvloop',
        'requests',
    ],
    packages=setuptools.find_packages(),
    package_data={
        '': [
            '*.tpl',
        ],
    },
    include_package_data=True,
)
