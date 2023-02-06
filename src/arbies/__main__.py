import sys
import os
import argparse
import asyncio
import toml
from arbies.manager import Manager
from typing import Optional


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='~/.arbies.toml')

    command_parser = parser.add_subparsers(dest='command')
    command_parser.required = True

    command_parser.add_parser('once')
    command_parser.add_parser('loop')

    args = parser.parse_args()

    config_path = os.path.expanduser(args.config)

    if not os.path.isfile(config_path):
        print(f'Could not find configuration file "{config_path}".')
        return 1

    manager = _get_manager(config_path)
    func: Optional = None

    if args.command == 'once':
        func = manager.render_once
    elif args.command == 'loop':
        func = manager.render_loop

    if func is not None:
        task = asyncio.create_task(func())
        try:
            await task
        except KeyboardInterrupt:
            task.cancel()
            await task

    return 0


def _get_manager(config_path) -> Optional[Manager]:
    with open(config_path, 'r') as config_file:
        return Manager.from_config(toml.load(config_file))


sys.exit(asyncio.run(main()))
