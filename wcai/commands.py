import logging
import sys

from wildcatting.theme import DefaultTheme

from .data import FieldWriter, UtilityEstimator


log = logging.getLogger("wildcatting-ai")


class FieldCommand:
    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("field", help="Generate oil field data")
        subparser.add_argument("--width", default=80, type=int,
                               help="oil field width")
        subparser.add_argument("--height", default=24, type=int,
                               help="oil field height")
        subparser.add_argument("--num", default=1,  type=int,
                               help="number of fields to generate")
        subparser.add_argument("--delim", default=" ", type=str,
                               help="ascii delimiter")
        subparser.add_argument("--inputs", choices=['prob', 'cost', 'tax'],
                               nargs='+', default=['prob', 'cost'],
                               help="input fields")
        subparser.add_argument("--output", choices=['utility'],
                               nargs='+', default='util',
                               help="output fields")
        subparser.add_argument("--file", type=str, default=None,
                               help="write to specified file")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        theme = DefaultTheme()
        val_func = UtilityEstimator(theme, args.width * args.height)
        fw = FieldWriter(args, theme, val_func)
        if args.file:
            with open(args.file, 'w') as f:
                fw.write(f)
        else:
            fw.write(sys.stdout)
