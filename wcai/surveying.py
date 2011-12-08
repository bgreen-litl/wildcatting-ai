import random
import neurolab as nl

from wildcatting.theme import DefaultTheme


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
    def __init__(self, nn):
        self.nn = nn

    def choose(self, region):
        """Choose a site to drill in; Return its index."""
        # uses probalistic wc-zooming
        outputs = self.nn.activate(region.inputs)
        tot_out = reduce(lambda x, y: x + y, outputs)
        r = random.uniform(0, 1)
        t = 0
        for i, o in enumerate(outputs):
            t += o / tot_out
            if r <= t:
                if region.scale == 1:
                    return i
                else:
                    return self.choose(region.zoom(i))
