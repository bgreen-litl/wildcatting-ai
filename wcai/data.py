import math
import random
import numpy as np

from wildcatting.model import OilField
from wildcatting.game import (OilFiller, PotentialOilDepthFiller,
                              ReservoirFiller, DrillCostFiller, TaxFiller)


rnd = random.Random()


def normalize(val, min_val, max_val, min_norm=-1, max_norm=1):
    return (((val - min_val) / (max_val - min_val)) *
            (max_norm - min_norm) + min_norm)


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
    @staticmethod
    def map(field, val_funcs=[], pos=(0, 0), size=None):
        if not size:
            size = (field.getWidth(), field.getHeight())

        region = Region()
        region.field = field
        region.size = size   # size of corresponding region in field
        region.scale = 1
        region.pos = pos
        region.wh = size  # width, height of the region

        x, y = pos
        for row in xrange(y, y + size[1]):
            for col in xrange(x, x + size[0]):
                site = field.getSite(row, col)
                vals = {}
                for vf in val_funcs:
                    vals[vf.header.lower()] = vf.value(site)
                region.sites.append(vals)
        return region

    @staticmethod
    def partition(field, scale, val_funcs):
        w = field.getWidth() / scale  # 10
        h = field.getHeight() / scale  # 3
        parts = []
        for i in xrange(w * h):
            part = Region()
            part.field = field
            part.size = (w, h)  # (10, 3)
            part.scale = 1
            (x, y) = (i % w, i / w)
            part.pos = (x, y)
            part.wh = (w, h)
            for row in xrange(y, y + h):
                for col in xrange(x, x + w):
                    site = field.getSite(row, col)
                    vals = {}
                    for vf in val_funcs:
                        vals[vf.header] = vf.value(site, scale)
                    part.sites.append(vals)
            parts.append(part)
        return parts

    @staticmethod
    def reduce(region, scale):
        reduct = Region()
        reduct.field = region.field
        reduct.size = region.wh
        reduct.scale = scale
        reduct.pos = region.pos
        reduct.wh = np.array(region.size) / scale

        # define the dimensions of the rectangle in the field
        fwh = 2.0 * np.array(region.wh) / (np.array(reduct.wh) + 1.0)
        # offsets between overlapped subregions
        ox, oy = fwh / 2.0
        # iterate across the overlapping regions
        fy = -oy
        for y in xrange(reduct.wh[1]):
            fy += oy
            fx = -ox
            for x in xrange(reduct.wh[0]):
                fx += ox
                avgs = Region.avgs(fx, fy, fwh, region)
                reduct.sites.append(avgs)
        return reduct

    @staticmethod
    def avgs(x, y, size, region):
        avgs = {}
        for val in region.sites[0].keys():
            avgs[val] = 0

        w, h = size
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

    def __init__(self):
        self.sites = []

    def __str__(self):
        str_ = ""
        for i, s in enumerate(self.sites):
            str_ += ("%s " % (int(s['prob'] * 10)))
            if (i + 1) % self.wh[0] == 0:
                str_ += "\n"
        str_ += "(Covering %s %s)" % self.size
        return str_

    def coords(self, idx):
        return np.array([idx % self.wh[0], idx / self.wh[0]])

    def inputs(self, vals):
        inputs = []
        for s in self.sites:
            for val in vals:
                inputs.append(s[val])
        return inputs

    def site(self, row, col):
        site = self.sites[row * self.wh[0] + col]
        return site


class ValueFunction:
    def __init__(self, theme, site_ct, normalize=False):
        self.theme = theme
        self.site_ct = site_ct
        self.normalize = normalize


class OilProbability(ValueFunction):
    header = "prob"

    def value(self, site, scale=1):
        prob = site.getProbability()
        if self.normalize:
            prob = normalize(prob, 0.0, 100.0)
        return prob


class DrillCost(ValueFunction):
    header = "cost"

    def value(self, site, scale=1):
        cost = site.getDrillCost()
        if self.normalize:
            cost = normalize(cost, self.theme.getMinDrillCost(),
                             self.theme.getMaxDrillCost())
        return cost


class Taxes(ValueFunction):
    header = "tax"

    def value(self, site, scale=1):
        tax = site.getTax()
        if self.normalize:
            tax = normalize(tax, self.theme.getMinTax(),
                            self.theme.getMaxTax())


# TODO normalization
class OilValue(ValueFunction):
    header = "val"

    def value(self, site, scale=1):
        price = self.theme.getOilPrices()._price
        reserves = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            reserves = reservoir.getReserves()
        return price * reserves


# TODO normalization
class OilReserves(ValueFunction):
    header = "bbl"

    def value(self, site, scale=1):
        reserves = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            reserves = reservoir.getReserves()
        return reserves


class OilPresence(ValueFunction):
    header = "wet"

    def value(self, site, scale=1):
        return 0.0 if site.getReservoir() is None else 1.0


class ReservoirSize(ValueFunction):
    header = "size"

    def value(self, site, scale=1):
        size = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            size = reservoir._size
            if self.normalize:
                size = normalize(size, 0, self.site_ct / (scale ** 2))
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

    def value(self, site, scale=1):
        price = self.theme.getOilPrices()._price
        cost = site.getDrillCost()
        pot = site.getPotentialOilDepth()
        oil = site.getOilFlag()

        # drill to the oil or to the bottom whichever comes first
        expense = cost * pot * 10.0 if oil else cost * 100.0

        # estimated max income that could be obtained from a real spindletop
        mean_reserves = self.theme.getMeanSiteReserves()

        expected = 0
        if site.getReservoir():
            reservoir = site.getReservoir()
            expected = reservoir.getReserves() * price

        # tanh serves as a squashing function for towards max_oil
        max_oil = 5 * mean_reserves * price
        utility = np.tanh((expected - expense) / max_oil)

        return utility
