import unittest

from os.path import exists, join

from wildcatting.model import OilField
from wildcatting.game import (Filler, OilFiller, DrillCostFiller,
                              ReservoirFiller, PotentialOilDepthFiller)
from wildcatting.theme import DefaultTheme

from wcai.agent import Agent, Surveying, Report, Drilling, Sales
from wcai.data import Region


# Bud Brigham is a geophysicist who believed in technology.
# He rode high and he fell hard.
dir = 'bud'


class OilMountainFiller(OilFiller):
    def getMaxPeaks(self):
        return 1

    def _generatePeaks(self, model):
        return [(40, 12)]


theme = DefaultTheme()
field = OilField(80, 24)
OilMountainFiller(theme).fill(field)
DrillCostFiller(theme).fill(field)
PotentialOilDepthFiller(theme).fill(field)
ReservoirFiller(theme).fill(field)


class AgentTest(unittest.TestCase):

    def test_init(self):
        Agent.init(dir)
        self.assertTrue(exists(join(dir, 'surveying')))
        self.assertTrue(exists(join(dir, 'report')))
        self.assertTrue(exists(join(dir, 'drilling')))
        self.assertTrue(exists(join(dir, 'sales')))
        self.assertTrue(exists(join(dir, 'probability')))
        self.assertTrue(exists(join(dir, 'drill_cost')))

    def test_load(self):
        Agent.load(dir)


class SurveyingTest(unittest.TestCase):

    def test_init(self):
        Surveying.init(dir)

    def test_load(self):
        Surveying.load(dir)

    def save(self):
        surveying = Surveying.init(dir)
        surveying.save()

    def test_choose(self):
        theme = DefaultTheme()
        field = OilField(80, 24)
        OilFiller(theme).fill(field)
        DrillCostFiller(theme).fill(field)
        PotentialOilDepthFiller(theme).fill(field)
        ReservoirFiller(theme).fill(field)

        surveying = Surveying.load(dir)

        coords = surveying.choose(field)
        surveying = Surveying.load(dir)
        region = Region.map(field)
        coords = surveying.choose(field)


class ReportTest(unittest.TestCase):

    def test_init(self):
        Report.init(dir)

    def test_load(self):
        Report.load(dir)


class DrillingTest(unittest.TestCase):

    def test_init(self):
        Drilling.init(dir)

    def test_load(self):
        Drilling.load(dir)


class SalesTest(unittest.TestCase):

    def test_init(self):
        Sales.init(dir)

    def test_load(self):
        Sales.load(dir)


if __name__ == "__main__":
    unittest.main()
