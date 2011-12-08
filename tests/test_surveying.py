import unittest

from wildcatting.model import OilField
from wildcatting.game import (Filler, OilFiller, DrillCostFiller, 
                              ReservoirFiller, PotentialOilDepthFiller)
from wildcatting.theme import DefaultTheme

import wcai.surveying

class SurveyingNNTest(unittest.TestCase):

    def test_init(self):
        nn = wcai.surveying.SurveyingNN()
        print nn


class RuntimeSurveyingPolicyTest(unittest.TestCase):

    def test_choose(self):
        theme = DefaultTheme()
        field = OilField(80, 24)
        OilFiller(theme).fill(field)
        DrillCostFiller(theme).fill(field)
        PotentialOilDepthFiller(theme).fill(field)
        ReservoirFiller(theme).fill(field)

        nn = wcai.surveying.SurveyingNN()
        pol = wcai.surveying.RuntimeSurveyingPolicy(nn)

        coords = pol.choose(field)
        ## TODO some tests on the results

        
if __name__ == "__main__":
    unittest.main()
