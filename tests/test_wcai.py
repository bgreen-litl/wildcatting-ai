import unittest

from wildcatting.model import OilField, Site
from wildcatting.game import Filler, OilFiller, DrillCostFiller, ReservoirFiller, PotentialOilDepthFiller
from wildcatting.theme import DefaultTheme
from wcai.data import Region, OilProbability, UtilityEstimator


class FlatFiller(Filler):
    def fill(self, field):
        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                site.setProbability(10)
                site.setDrillCost(10)
                site.setTax(10)


class AlternatingFiller(Filler):
    def fill(self, field):
        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                site.setProbability(10 * (row % 2))
                site.setDrillCost(10 * (row % 2))
                site.setTax(10 * (row % 2))


class RegionTest(unittest.TestCase):

    def test_fill_flat(self):
        theme = DefaultTheme()
        for width, height in [(80,24), (40, 12), (20, 6)]:
            field = OilField(width, height)
            FlatFiller().fill(field)
            map = Region.map(field)
            val_funcs = [OilProbability(theme, width*height)]
            region = Region.reduce(map, 10, 3, val_funcs)
            self.assertEquals(len(region.sites), 30)
            for i in xrange(30):
                self.assertEquals(region.sites[i]['prob'], 10.0)

    def test_visualize(self):
        theme = DefaultTheme()
        for width, height in [(40, 12), (20, 6)]:
            field = OilField(width, height)
            OilFiller(theme).fill(field)
            DrillCostFiller(theme).fill(field)
            PotentialOilDepthFiller(theme).fill(field)
            ReservoirFiller(theme).fill(field)
            map = Region.map(field)
            print map
            val_funcs = [OilProbability(theme, width * height)]
            region = Region.reduce(map, 10, 3, val_funcs)
            self.assertEquals(len(region.sites), 30)
            print region


if __name__ == "__main__":
    unittest.main()
