#!/usr/bin/env python


from random import Random

from wildcatting.model import OilField
from wildcatting.game import OilFiller, DrillCostFiller, TaxFiller, \
                             PotentialOilDepthFiller, ReservoirFiller
from wildcatting.theme import DefaultTheme


width = 80
height = 24
theme = DefaultTheme()
fields = 1
filename = 'q_surveying_data.txt'


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
def estimate_utility(site, width, height, theme, oil_price):
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
    mean_reserves = theme.getMeanSiteReserves()
    max_oil = width * height / 8 / 2.0 * mean_reserves * oil_price

    expected = 0
    if site.getReservoir():
        reservoir = site.getReservoir()
        reserves = reservoir.getReserves()
        size = reservoir._size

        # oil price, rough peak oil, normalize against max_oil. take the min 
        # in case our max_oil estimation turns out to be too low (unlikely)
        expected = min(size / 2.0 * reserves * oil_price, max_oil)

    utility = (expected - expense) / max_oil

    return utility


def generate(width, height, theme, num, f):
    rnd = Random()

    oil_filler = OilFiller(theme)
    depth_filler = PotentialOilDepthFiller(theme)
    res_filler = ReservoirFiller(theme)
    cost_filler = DrillCostFiller(theme)
    tax_filler = TaxFiller(theme)

    for i in xrange(num):
        oil_field = OilField(width, height)
        oil_filler.fill(oil_field)
        depth_filler.fill(oil_field)
        res_filler.fill(oil_field)
        cost_filler.fill(oil_field)
        tax_filler.fill(oil_field)

        oil_price = theme.getOilPrices().next()

        for row in xrange(height):
            for col in xrange(width):
                site = oil_field.getSite(row, col)
                prob = site.getProbability() / 100.0
                cost = site.getDrillCost() / float(theme.getMaxDrillCost())
                f.write("%s %s " % (prob, cost))

        for row in xrange(height):
            for col in xrange(width):
                site = oil_field.getSite(row, col)
                util = estimate_utility(site, width, height, theme, oil_price)
                f.write("%s " % util)

        f.write('\n')


if __name__ == '__main__':
    with open(filename, 'w') as f:
        generate(width, height, theme, fields, f)
