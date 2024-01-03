import sys
import os
import argparse
import asyncio
from asyncio.exceptions import CancelledError
import toml
from arbies.manager import Manager


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

    await manager.render_loop() if args.command == 'loop' else manager.render_once()
    await manager.shutdown()

    return 0


def _get_manager(config_path) -> Manager | None:
    with open(config_path, 'r') as config_file:
        return Manager(**toml.load(config_file))


sys.exit(asyncio.run(main()))
