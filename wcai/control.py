#!/usr/bin/env python

import argparse
import logging
import sys

from . import commands

parser = argparse.ArgumentParser(description="wcai control")
parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

subparsers = parser.add_subparsers(title="Commands")
commands.InitCommand.add_subparser(subparsers)
commands.TrainCommand.add_subparser(subparsers)
commands.SimulateCommand.add_subparser(subparsers)
commands.LearnCommand.add_subparser(subparsers)
commands.PlayCommand.add_subparser(subparsers)


def main():
    args = parser.parse_args()

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.root.addHandler(console)

    if args.debug:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)

    try:
        args.run(args)
    except KeyboardInterrupt:
        print
        sys.exit(1)


if __name__ == "__main__":
    main()
