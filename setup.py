import setuptools


setuptools.setup(
    name='tasker',
    version='0.0.2',
    author='gal@intsights.com',
    author_email='gal@intsights.com',
    description=('A fast, simple, task distribution library'),
    zip_safe=True,
    install_requires=[
        'redis',
        'hiredis',
        'redis-py-cluster',
        'msgpack-python',
        'aiohttp',
        'jinja2',
        'pyzmq',
    ],
    packages=setuptools.find_packages(),
)
