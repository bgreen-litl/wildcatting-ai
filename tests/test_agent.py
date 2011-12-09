import unittest

from os.path import exists, join

from wildcatting.model import OilField
from wildcatting.game import (Filler, OilFiller, DrillCostFiller, 
                              ReservoirFiller, PotentialOilDepthFiller)
from wildcatting.theme import DefaultTheme

from wcai.agent import Agent, Surveying, Report, Drilling, Sales


# Bud Brigham is a geophysicist who believed in technology.
# He rode high and he fell hard.
dir = 'bud'


class AgentTest(unittest.TestCase):

    def test_init(self):
        agent = Agent.init(dir)
        self.assertTrue(exists(join(dir, 'surveying')))
        self.assertTrue(exists(join(dir, 'report')))
        self.assertTrue(exists(join(dir, 'drilling')))
        self.assertTrue(exists(join(dir, 'sales')))

    def test_load(self):
        agent = Agent.load(dir)


class SurveyingTest(unittest.TestCase):

    def test_init(self):
        surveying = Surveying.init(dir)

    def test_load(self):
        surveying = Surveying.load(dir)

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
        ## TODO some tests on the results
        

class ReportTest(unittest.TestCase):

    def test_init(self):
        report = Report.init(dir)

    def test_load(self):
        report = Report.load(dir)


class DrillingTest(unittest.TestCase):

    def test_init(self):
        drilling = Drilling.init(dir)

    def test_load(self):
        drilling = Drilling.load(dir)


class SalesTest(unittest.TestCase):

    def test_init(self):
        surveying = Sales.init(dir)

    def test_load(self):
        drilling = Sales.load(dir)


if __name__ == "__main__":
    unittest.main()
