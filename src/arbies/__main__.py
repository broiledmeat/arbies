import sys
import os
import argparse
import toml
from arbies.manager import Manager
from typing import Optional


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='~/.arbies.json')

    command_parser = parser.add_subparsers(dest='command')
    command_parser.required = True

    command_parser.add_parser('once')
    command_parser.add_parser('loop')

    args = parser.parse_args()

    config_path = os.path.expanduser(args.config)

    if not os.path.isfile(config_path):
        print(f'Could not find configuration file "{config_path}".')
        return 1

    if args.command == 'once':
        if manager := _get_manager(config_path):
            manager.render_once()
    elif args.command == 'loop':
        from arbies.suppliers.filesystem import add_on_changed

        manager: Optional[Manager] = None

        def cancel_loop():
            if manager is not None:
                manager.cancel_loop()

        add_on_changed(config_path, cancel_loop)

        try:
            while True:
                manager = _get_manager(config_path)
                manager.loop()
        except KeyboardInterrupt:
            if manager is not None:
                manager.cancel_loop()

    return 0


def _get_manager(config_path) -> Optional[Manager]:
    with open(config_path, 'r') as config_file:
        return Manager.from_config(toml.load(config_file))


sys.exit(main())
