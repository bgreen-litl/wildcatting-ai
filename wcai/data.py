import random

from wildcatting.model import OilField
from wildcatting.game import OilFiller, DrillCostFiller, TaxFiller, \
                             PotentialOilDepthFiller, ReservoirFiller


rnd = random.Random()


def normalize(val, min_val, max_val):
    return (val - min_val) / float(max_val - min_val)


class FieldWriter:
    def __init__(self, args, theme, val_funcs):
        self.args = args
        self.theme = theme
        self.val_funcs = val_funcs

    def write_headers(self, site_ct, out):
        for i in xrange(site_ct):
            if 'prob' in self.args.inputs:
                out.write("PROB_%s%s" % (i, self.args.delim))
            if 'cost' in self.args.inputs:
                out.write("COST_%s%s" % (i, self.args.delim))
            if 'tax' in self.args.inputs:
                out.write("TAX_%s%s" % (i, self.args.delim))

        for i in xrange(site_ct):
            for vf in self.val_funcs:
                out.write("%s_%s%s" % (vf.header, i, self.args.delim))

    def write_input(self, field, out):
        delim = self.args.delim
        mindc = self.theme.getMinDrillCost()
        maxdc = self.theme.getMaxDrillCost()
        mintax = self.theme.getMinTax()
        maxtax = self.theme.getMaxTax()
        for row in xrange(self.args.height):
            for col in xrange(self.args.width):
                site = field.getSite(row, col)
                prob = cost = tax = ""
                if 'prob' in self.args.inputs:
                    p = site.getProbability()
                    prob = "%s%s" % (normalize(p, 0, 100), delim)
                if 'cost' in self.args.inputs:
                    dc = site.getDrillCost()
                    cost = "%s%s" % (normalize(dc, mindc, maxdc), delim)
                if 'tax' in self.args.inputs:
                    t = site.getTax()
                    tax = "%s%s" % (normalize(t, mintax, maxtax), delim)
                out.write("%s%s%s" % (prob, cost, tax))

    def write_output(self, field, out):
        for row in xrange(self.args.height):
            for col in xrange(self.args.width):
                site = field.getSite(row, col)
                for vf in self.val_funcs:
                    out.write("%s%s" % (vf.value(site), self.args.delim))

    def write(self, out):
        oil_filler = OilFiller(self.theme)
        depth_filler = PotentialOilDepthFiller(self.theme)
        res_filler = ReservoirFiller(self.theme)
        cost_filler = DrillCostFiller(self.theme)
        tax_filler = TaxFiller(self.theme)

        if not self.args.no_headers:
            self.write_headers(self.args.width * self.args.height, out)

        for i in xrange(self.args.num):
            field = OilField(self.args.width, self.args.height)
            oil_filler.fill(field)
            depth_filler.fill(field)
            res_filler.fill(field)
            cost_filler.fill(field)
            tax_filler.fill(field)

            self.write_input(field, out)
            self.write_output(field, out)
            out.write('\n')


class ValueFunction:
    def __init__(self, theme, site_ct):
        self.theme = theme
        self.site_ct = site_ct


class OilValue(ValueFunction):
    header = "VAL"

    def value(self, site):
        price = self.theme.getOilPrices()._price
        reserves = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            reserves = reservoir.getReserves()
        return price * reserves


class OilReserves(ValueFunction):
    header = "BBL"

    def value(self, site):
        reserves = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            reserves = reservoir.getReserves()
        return reserves


class OilPresence(ValueFunction):
    header = "WET"

    def value(self, site):
        return 0 if site.getReservoir() is None else 1


class ReservoirSize(ValueFunction):
    header = "SIZE"

    def value(self, site):
        size = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            size = reservoir._size
        return size


## estimate the utility of surveying in the specified site. in wilcatting, the
## utility is the expected future monetary gain. this is a heuristic function
## that makes a number of questionable assumptions, but it is informed by
## actual data from a true generated oil field, including the size of oil
## reserves at the site in question. what it cannot accurately predict is
## future decisions. it assumes the fixed policy of always drilling to the
## bottom at the surveyed site. neither does it take into account the number
## weeks remaining in the game. nonetheless, when compared in a relative
## sense this estimate should do a decent job predicting better or worse
## sites to survey
class UtilityEstimator(ValueFunction):
    header = "UTIL"

    def value(self, site):
        price = self.theme.getOilPrices()._price
        cost = site.getDrillCost()
        pot = site.getPotentialOilDepth()
        oil = site.getOilFlag()

        # drill to the oil or to the bottom whichever comes first
        # normalize against max_oil so expense and income are on same scale
        expense = cost * pot * 10.0 if oil else cost * 100.0

        # estimated max income that could be obtained from a real spindletop
        # assumptions:
        #     reservoir could be at most 1/8 of the field size
        #     peak oil (very rough formulation)
        #     reserves would average out to the per site mean
        mean_reserves = self.theme.getMeanSiteReserves()
        max_oil = self.site_ct / 8 / 2.0 * mean_reserves * price

        expected = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            reserves = reservoir.getReserves()

            size = reservoir._size

            # oil price, rough peak oil, normalize against max_oil. take the
            # min in case our max_oil estimation turns out to be too low
            expected = min(size / 2.0 * reserves * price, max_oil)

        utility = (expected - expense) / max_oil

        return utility
