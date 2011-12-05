import random

from wildcatting.model import OilField
from wildcatting.game import OilFiller, DrillCostFiller, TaxFiller, \
                             PotentialOilDepthFiller, ReservoirFiller


rnd = random.Random()


def normalize(val, min_val, max_val):
    return (val - min_val) / float(max_val - min_val)


class FieldWriter:
    def __init__(self, args, theme, estimator):
        self.args = args
        self.theme = theme
        self.estimator = estimator

    def write_input(self, field, out):
        delim = self.args.delim
        mindc = self.theme.getMinDrillCost()
        maxdc = self.theme.getMaxDrillCost()
        mintax = self.theme.getMinTax()
        maxtax = self.theme.getMaxTax()
        input = self.args.inputs

        for row in xrange(self.args.height):
            for col in xrange(self.args.width):
                site = field.getSite(row, col)
                p = site.getProbability()
                dc = site.getDrillCost()
                t = site.getTax()
                prob = cost = tax = ""
                if 'prob' in self.args.inputs:
                    prob = "%s%s" % (p / 100.0, delim)
                if 'cost' in self.args.inputs:
                    cost = "%s%s" % (normalize(dc, mindc, maxdc), delim)
                if 'tax' in self.args.inputs:
                    tax = "%s%s" % (normalize(t, mintax, maxtax), delim)
                out.write("%s%s%s" % (prob, cost, tax))

    def write(self, out):
        oil_filler = OilFiller(self.theme)
        depth_filler = PotentialOilDepthFiller(self.theme)
        res_filler = ReservoirFiller(self.theme)
        cost_filler = DrillCostFiller(self.theme)
        tax_filler = TaxFiller(self.theme)

        for i in xrange(self.args.num):
            oil_field = OilField(self.args.width, self.args.height)
            oil_filler.fill(oil_field)
            depth_filler.fill(oil_field)
            res_filler.fill(oil_field)
            cost_filler.fill(oil_field)
            tax_filler.fill(oil_field)

            oil_price = self.theme.getOilPrices().next()

            self.write_input(oil_field, out)

            for row in xrange(self.args.height):
                for col in xrange(self.args.width):
                    site = oil_field.getSite(row, col)
                    util = self.estimator.estimate(site, self.args.width, \
                                                   self.args.height)
                    out.write("%s%s" % (util, self.args.delim))
            out.write('\n')


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

class UtilityEstimator:
    def __init__(self, theme):
        self.theme = theme

    def estimate(self, site, width, height):
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
        max_oil = width * height / 8 / 2.0 * mean_reserves * price

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
