from setuptools import setup

setup(name='arbies',
      version='1.0',
      packages=['arbies'],
      python_requires='>3.12',
      requires=[
          'aiohttp',
          'cairosvg',
          'croniter',
          'natsort',
          'Pillow',
          'pytz',
          'toml',
          'watchdog',
      ])
