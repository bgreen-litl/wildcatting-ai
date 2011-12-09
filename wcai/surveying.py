import random
import neurolab as nl

from wildcatting.theme import DefaultTheme

from .data import Region, UtilityEstimator

rnd = random.Random()
theme = DefaultTheme()


class SurveyingNN():

    def __init__(self, width=10, height=3, in_fields=2, out_fields=1):

        inputs = width * height * in_fields
        outputs = width * height * out_fields
        hiddens = int(2 * (inputs + outputs) / 3.0)

        self.net = nl.net.newff([[0.0, 1.0]] * inputs, [hiddens, outputs])

    def activate(self, input):
        return self.net.sim([input])[0]


class Q_surveying:
    """Maintains mappings from field, site pairs to expected utilities"""

    def __init__(self, nn):
        self.nn = nn

    def eval(self, field, site):
        """Return the expected utility of surveying a site in a field"""
        region, idx = self.region(field, site)
        o = self.nn.activate(region.inputs())
        return o[idx]

    def region(self, field, site):
        """Return the region a site is in and its index withing that region"""
        pass


class QLearningSurveyingPolicy:
    def choose(self, field):
        return random.sample(field.sites, 1)[0]


class RuntimeSurveyingPolicy:
    val_funcs = [UtilityEstimator(theme, 80 * 24, normalize=True)]

    def __init__(self, nn):
        self.nn = nn

    @staticmethod
    def select_output(outputs):
        tot_out = reduce(lambda x, y: x + y, outputs)
        r = random.uniform(0, 1)
        t = 0
        for i, o in enumerate(outputs):
            t += o / tot_out
            if r <= t:
                return i

    def select(self, region):
        inputs = region.inputs(['prob', 'cost'])
        outputs = self.nn.activate(inputs)
        return RuntimeSurveyingPolicy.select_output(outputs)

    # region is some 1:1 subset of the field
    def _choose(self, region, scale):
        if scale == 1:
            i = self.select(region)
            c = (i % region.width, i / region.height)
            x = region.center[0] - region.size[0] / 2 + c[0]
            y = region.center[1] - region.size[1] / 2 + c[1]
            return x, y

        r = Region.reduce(region, scale)
        i = self.select(r)
        map = Region.map(region.field, RuntimeSurveyingPolicy.val_funcs,
                         r.center, (region.width / 2, region.height / 2))
        return self._choose(map, scale / 2)

    def choose(self, field):
        map = Region.map(field, RuntimeSurveyingPolicy.val_funcs)
        coords = self._choose(map, 8)
        return coords
