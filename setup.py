from distutils.core import setup

setup(name='arbies',
      version='1.0',
      packages=['arbies'],
      requires=['aiohttp', 'Pillow', 'cairosvg', 'natsort', 'watchdog', 'toml', 'croniter'])
