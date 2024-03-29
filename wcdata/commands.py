import logging
import sys

from wildcatting.theme import DefaultTheme

from wcai.data import (Simulator, Region, OilProbability, DrillCost, Taxes,
                       OilPresence, OilReserves, ReservoirSize, OilValue,
                       UtilityEstimator, normalize)


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

    val_map = {'prob': OilProbability, 'cost': DrillCost, 'tax': Taxes,
               'wet': OilPresence, 'bbl': OilReserves, 'size': ReservoirSize,
               'val': OilValue, 'util': UtilityEstimator}

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
        subparser.add_argument("--inputs", choices=FieldCommand.val_map.keys(),
                               nargs='+', default=['prob', 'cost'],
                               help="input fields")
        subparser.add_argument("--outputs",
                               choices=FieldCommand.val_map.keys(), nargs='+',
                               default=['wet'], help="output fields")
        subparser.add_argument("--normalize", action="store_true",
                               default=False, help="normalize between 0 and 1")
        subparser.add_argument("--reduce", type=int, default=1,
                               help="scale down by the specified factor")
        subparser.add_argument("--partition", type=int,
                               help="output partitions of a larger field")
        subparser.add_argument("--file", type=str, default=None,
                               help="write to specified file")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        theme = DefaultTheme()

        ins = []
        for i in args.inputs:
            ins.append(FieldCommand.val_map[i](theme,
                                               args.width * args.height,
                                               args.normalize))
        outs = []
        for o in args.outputs:
            outs.append(FieldCommand.val_map[o](theme,
                                                args.width * args.height,
                                                args.normalize))

        fw = FieldWriter(args, theme, ins, outs)
        if args.file:
            with open(args.file, 'w') as f:
                fw.write(f)
        else:
            fw.write(sys.stdout)


class FieldWriter:
    def __init__(self, args, theme, ins, outs):
        self.args = args
        self.theme = theme
        self.ins = ins
        self.outs = outs

    def write_headers(self, site_ct, out):
        # inputs
        for site in xrange(site_ct):
            for i in self.ins:
                out.write("%s_%s%s" % (i.key.upper(), site,
                                       self.args.delim))
        # outputs
        for site in xrange(site_ct):
            for o in self.outs:
                out.write("%s_%s%s" % (o.key.upper(), site,
                                       self.args.delim))

    def write_values(self, region, val_funcs, out):
        for site in region.sites:
            for vf in val_funcs:
                out.write("%s%s" % (site[vf.key], self.args.delim))

    def write(self, out):
        if not self.args.no_headers:
            site_ct = (self.args.width * self.args.height /
                       self.args.reduce ** 2)
            if self.args.partition:
                site_ct /= self.args.partition ** 2
            self.write_headers(site_ct, out)

        sim = Simulator(DefaultTheme())
        for i in xrange(self.args.num):
            field = sim.field(self.args.width, self.args.height)
            val_funcs = self.ins + self.outs
            region = Region.map(field, val_funcs)

            if self.args.partition:
                regions = region.partition(field, self.args.partition,
                                           val_funcs)
            else:
                regions = [region]

            if self.args.reduce != 1:
                regions = [Region.reduce(r, self.args.reduce) for r in regions]

            for region in regions:
                self.write_values(region, self.ins, out)
                self.write_values(region, self.outs, out)
                out.write('\n')
