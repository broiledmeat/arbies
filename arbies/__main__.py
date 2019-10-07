import sys
import os
import argparse
import json
from arbies.manager import Manager


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

    with open(config_path, 'r') as config_file:
        manager = Manager.from_config(json.load(config_file))

    if args.command == 'once':
        manager.render_once()
    elif args.command == 'loop':
        manager.loop()

    return 0


sys.exit(main())
