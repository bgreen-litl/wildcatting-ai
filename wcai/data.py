import math
import random

from wildcatting.model import OilField
from wildcatting.game import (OilFiller, PotentialOilDepthFiller,
                              ReservoirFiller, DrillCostFiller, TaxFiller)


rnd = random.Random()


def normalize(val, min_val, max_val):
    return (val - min_val) / float(max_val - min_val)


class Simulator:
    def __init__(self, theme):
        self.theme = theme
        self.fillers = [OilFiller(self.theme),
                        PotentialOilDepthFiller(self.theme),
                        ReservoirFiller(self.theme),
                        DrillCostFiller(self.theme), TaxFiller(self.theme)]

    def field(self, width, height):
        field = OilField(width, height)
        map(lambda x: x.fill(field), self.fillers)
        return field


class Region:
    def __init__(self):
        self.sites = []

    def __str__(self):
        str_ = ""
        for i, s in enumerate(self.sites):
            str_ += ("%0.0f " % (s['prob']))
            if (i + 1) % self.width == 0:
                str_ += "\n"
        return str_

    @staticmethod
    def map(field, val_funcs=[], center=None, size=None):
        if not center:
            center = (field.getWidth() / 2, field.getHeight() / 2)
        if not size:
            size = (field.getWidth(), field.getHeight())

        region = Region()
        region.field = field
        region.size = size   # size of the region in the field
        region.scale = 1
        region.center = center
        region.width = size[0]
        region.height = size[1]

        x = center[0] - size[0] / 2
        y = center[1] - size[1] / 2
        w, h = size

        for row in xrange(y, y + h):
            for col in xrange(x, x + w):
                site = field.getSite(row, col)
                vals = {}
                for vf in val_funcs:
                    vals[vf.header.lower()] = vf.value(site)
                region.sites.append(vals)
        return region

    @staticmethod
    def reduce(region, scale):
        reduct = Region()
        reduct.field = region.field
        reduct.size = (region.width / scale, region.height / scale)
        reduct.scale = scale
        reduct.center = region.center
        reduct.width = region.size[0] / scale
        reduct.height = region.size[1] / scale

        # define the dimensions of the rectangle in the field
        fw = 2.0 * region.width / (reduct.width + 1.0)
        fh = 2.0 * region.height / (reduct.height + 1.0)
        # offsets between overlapped subregions
        ox, oy = fw / 2.0, fh / 2.0
        # iterate across the overlapping regions
        fy = -oy
        for y in xrange(reduct.height):
            fy += oy
            fx = -ox
            for x in xrange(reduct.width):
                fx += ox
                avgs = Region.avgs(fx, fy, fw, fh, region)
                reduct.sites.append(avgs)
        return reduct

    @staticmethod
    def avgs(x, y, w, h, region):
        avgs = {}
        for val in region.sites[0].keys():
            avgs[val] = 0

        x_range = int(math.ceil(x + w) - math.floor(x))
        y_range = int(math.ceil(y + h) - math.floor(y))
        for row in xrange(y_range):
            for col in xrange(x_range):
                site = region.site(int(math.floor(y)) + row,
                                   int(math.floor(x)) + col)
                for val in site.keys():
                    avgs[val] += site[val]

        area = x_range * y_range
        for val in avgs.keys():
            avgs[val] /= area
        return avgs

    def inputs(self, vals):
        inputs = []
        for s in self.sites:
            for val in vals:
                inputs.append(s[val])
        return inputs

    def site(self, row, col):
        site = self.sites[row * self.width + col]
        return site


class ValueFunction:
    def __init__(self, theme, site_ct, normalize=False):
        self.theme = theme
        self.site_ct = site_ct
        self.normalize = normalize


class OilProbability(ValueFunction):
    header = "prob"

    def value(self, site):
        prob = site.getProbability()
        if self.normalize:
            prob = normalize(prob, 0.0, 100.0)
        return prob


class DrillCost(ValueFunction):
    header = "cost"

    def value(self, site):
        cost = site.getDrillCost()
        if self.normalize:
            cost = normalize(cost, self.theme.getMinDrillCost(),
                             self.theme.getMaxDrillCost())
        return cost


class Taxes(ValueFunction):
    header = "tax"

    def value(self, site):
        tax = site.getTax()
        if self.normalize:
            tax = normalize(tax, self.theme.getMinTax(),
                            self.theme.getMaxTax())


# TODO normalization
class OilValue(ValueFunction):
    header = "val"

    def value(self, site):
        price = self.theme.getOilPrices()._price
        reserves = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            reserves = reservoir.getReserves()
        return price * reserves


# TODO normalization
class OilReserves(ValueFunction):
    header = "bbl"

    def value(self, site):
        reserves = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            reserves = reservoir.getReserves()
        return reserves


class OilPresence(ValueFunction):
    header = "wet"

    def value(self, site):
        return 0.0 if site.getReservoir() is None else 1.0


class ReservoirSize(ValueFunction):
    header = "size"

    def value(self, site):
        size = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            size = reservoir._size
            if self.normalize:
                size = normalize(size, 0, self.site_ct)
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
    header = "util"

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
