import logging
import sys

from wildcatting.theme import DefaultTheme

from .data import OilPresence, OilReserves, ReservoirSize, OilValue, \
    UtilityEstimator, FieldWriter, normalize


log = logging.getLogger("wildcatting-ai")


class OilPriceCommand:
    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("oilprice", 
                                      help="Generate oil price data")
        subparser.add_argument("--weeks", default=52, type=int,
                               help="number of weeks to generate prices")
        subparser.add_argument("--normalize", action="store_true",
                               default=False, help="normalize between 0 and 1")
        subparser.add_argument("--file", type=str, default=None,
                               help="write to specified file")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def write(args, out):
        theme = DefaultTheme()
        prices = theme.getOilPrices()
        oil_min = prices._minPrice
        oil_max = prices._maxPrice
        for i in xrange(args.weeks):
            price = theme.getOilPrices().next()
            if args.normalize:
                price = normalize(price, oil_min, oil_max)
            out.write('%s\n' % price)

    @staticmethod
    def run(args):
        if args.file:
            with open(args.file, 'w') as f:
                OilPriceCommand.write(args, f)
        else:
            OilPriceCommand.write(args, sys.stdout)


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
        subparser.add_argument("--no-headers", action="store_true")
        subparser.add_argument("--delim", default=" ", type=str,
                               help="ascii delimiter")
        subparser.add_argument("--inputs", choices=['prob', 'cost', 'tax'],
                               nargs='+', default=['prob', 'cost'],
                               help="input fields")
        subparser.add_argument("--outputs", choices=['wet', 'bbl',
                                                    'size', 'val',
                                                    'util'],
                               nargs='+', default='wet',
                               help="output fields")
        subparser.add_argument("--normalize", action="store_true",
                               default=False, help="normalize between 0 and 1")
        subparser.add_argument("--file", type=str, default=None,
                               help="write to specified file")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        theme = DefaultTheme()
        val_funcs = []
        if 'wet' in args.outputs:
            val_funcs.append(OilPresence(theme, args.width * args.height))
        if 'bbl' in args.outputs:
            val_funcs.append(OilReserves(theme, args.width * args.height))
        if 'size' in args.outputs:
            val_funcs.append(ReservoirSize(theme, args.width * args.height))
        if 'val' in args.outputs:
            val_funcs.append(OilValue(theme, args.width * args.height))
        if 'util' in args.outputs:
            val_funcs.append(UtilityEstimator(theme, args.width * args.height))

        fw = FieldWriter(args, theme, val_funcs)
        if args.file:
            with open(args.file, 'w') as f:
                fw.write(f)
        else:
            fw.write(sys.stdout)
