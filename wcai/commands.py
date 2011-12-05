import logging
import sys

from wildcatting.theme import DefaultTheme

from .data import FieldWriter, UtilityEstimator


log = logging.getLogger("wildcatting-ai")


class FieldCommand:
    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("field", help="generate oil field data")
        subparser.add_argument("--width", default=80, type=int,
                               help="field width")
        subparser.add_argument("--height", default=24, type=int,
                               help="field height")
        subparser.add_argument("--num", default=1,  type=int,
                               help="number of fields to generate")
        subparser.add_argument("--delim", default=" ", type=str,
                               help="ascii delimiter")
        subparser.add_argument("--inputs", choices=['prob', 'cost', 'tax'],
            nargs='+', default=['prob', 'cost'],
            help="specify input fields from ['prob','cost','tax']")
        subparser.add_argument("--output", choices=['utility'],
                               default='util',
                               help="specify output fields from ['util']")
        subparser.add_argument("--file", type=str, default=None,
                               help="write to specified file")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        theme = DefaultTheme()
        fw = FieldWriter(args, theme, UtilityEstimator(theme))
        if args.file:
            with open(args.file, 'w') as f:
                fw.write(f)
        else:
            fw.write(sys.stdout)
