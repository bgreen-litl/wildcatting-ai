import os
import random
import numpy as np
import neurolab as nl

from os.path import join, exists

from wildcatting.theme import DefaultTheme

from .data import OilProbability, DrillCost, Region


theme = DefaultTheme()


# Components are decision making entities which are currently all backed by
# neural networks. The Component object provides a common interface for
# initializing, saving, loading and training these components. While the RL
# components (Surveying, Report, Drilling, and Sales) are intended to be
# trained via Q-learning, they all support supervised learning based on
# training data files. The purpose of this is threefold: testing, proof of
# concept, and bootstrap.
#
# In the bootstrap case, an NN may even be trained on a smaller set of inputs
# than will be provided at gameplay time. Additional initially zero-weighted
# inputs may be inserted with the weights for those inputs learned only
# through RL.
class Component:
    @classmethod
    def init(cls, agent):
        comp = cls(join(agent, cls.name))

        training_dir = join(comp.dir, 'training')
        if not exists(training_dir):
            os.makedirs(training_dir)

        hiddens = int(2 * (cls.inputs + cls.outputs) / 3.0)
        comp.nn = nl.net.newff([[0.0, 1.0]] * cls.inputs,
                               [hiddens, cls.outputs])
        nl.init.init_rand(comp.nn.layers[0])
        nl.init.init_rand(comp.nn.layers[1])
        comp.save()
        return comp

    @classmethod
    def load(cls, agent):
        dir = join(agent, cls.name)
        comp = cls(dir)
        comp.nn = nl.load(join(dir, 'utility.net'))
        return comp

    def __init__(self, dir):
        self.dir = dir

    def save(self):
        self.nn.save(join(self.dir, 'utility.net'))

    def train(self, epochs, show, goal):
        inp = []
        out = []
        # TODO support numpy binary datafiles
        dir = join(self.dir, 'training')
        for tf in os.listdir(dir):
            data = np.loadtxt(join(dir, tf))
            for d in data:
                inp.append(d[:self.inputs])
                out.append(d[self.inputs:])
        nl.train.train_rprop(self.nn, inp, out, epochs=epochs, show=show,
                             goal=goal)
        self.nn.save(join(self.dir, 'utility.net'))


class Surveying(Component):
    """Responsible for selecting a site to survey"""
    name = 'surveying'
    # TODO incorporate drill cost input and expected utility output
    inputs = 60  # prob, cost
    outputs = 30
    val_funcs = [OilProbability(theme, 80 * 24, normalize=True),
                 DrillCost(theme, 80 * 24, normalize=True)]

    # Select the site to survey from a region of the correct size to apply
    # directly to the NN. Chooses the site which corresponds to the highest
    # output value of the NN.
    def _choose_nn(self, region):
        inputs = region.inputs(['prob', 'cost'])
        outputs = self.nn.sim([inputs])[0]
        print outputs
        i = np.argmax(outputs)
        print "Chose %s (%s)" % (i, outputs[i])
        return i

    # Choose a site to survey from the specified region of the field. The
    # region here is always at 1:1 but varies in size. The scale is the factor
    # by which the region must be reduced in order to apply the NN.
    def _choose(self, region, scale):
        if scale == 1:
            i = self._choose_nn(region)
            return region.pos + region.coords(i)

        r = Region.reduce(region, scale)
        print r
        i = self._choose_nn(r)

        # map to field coordinates
        c = region.pos + r.coords(i) * ([scale] * 2) + ([scale / 2] * 2)

        # zoom in on the subsequent region, keeping its border in bounds
        w, h = np.array(region.wh) / 2
        x = min(max(0, c[0] - w / 2), region.field.getWidth() - w - 1)
        y = min(max(0, c[1] - h / 2), region.field.getHeight() - h - 1)

        map = Region.map(region.field, Surveying.val_funcs, (x, y), (w, h))
        return self._choose(map, scale / 2)

    def choose(self, field):
        """Choose a site to survey in the specified field based on nn output"""
        map = Region.map(field, Surveying.val_funcs)
        coords = self._choose(map, 8)
        return coords

    @staticmethod
    def highest_prob(field):
        """Choose the site with the highest known probability"""
        bp = 0
        w = field.getWidth()
        h = field.getHeight()
        # Consider all the sites, but don't favor the upper left
        start_row = random.randint(0, h)
        start_col = random.randint(0, w)
        for row in xrange(start_row, start_row + h):
            for col in xrange(start_col, start_col + w):
                site = field.getSite(row % h, col % w)
                if site.isSurveyed():
                    p = site.getProbability()
                    if p > bp:
                        bc = (col % w, row % h)
                        bp = p
        return bc


class Report(Component):
    """Responsible for deciding whether to drill given a Surveyor's Report"""
    name = 'report'
    inputs = 4   # prob, cost, tax
    outputs = 2  # expected utility of drilling and of not drilling


class Drilling(Component):
    """Responsible for deciding whether to drill 10 more meters"""
    name = 'drilling'
    inputs = 3   # cost, depth, expected depth
    outputs = 2  # expected utiltiy of drilling and of not drilling


class Sales(Component):
    """Responsible for deciding whether to sell a given well"""
    name = 'sales'
    inputs = 3   # income, tax, age
    outputs = 2  # expected utility of selling and of not selling


# The Probability and DrillCost components are backed by autoassociative
# neural networks. The task of these NNs is to guess at a complete distribution
# given the limited known inputs of surveyed sites.
#
# Unlike the supervised learning components, these are intended to be trained
# by supervised learning only with no modifications applied during
# reinforcement training. These networks need to be trained on thousands of
# generated, fully known probability or drill cost distributions.
#
# Performing this on a full 80x24 grid seems to be prohibitively costly, so
# the proposed algorithm operates instead on partitions of the full field.
# Here's how it works:
#
# The training data is based on thousands of 10x3 partitions of full 80x24
# generated fields with the inputs and outputs being the same, normalize 'prob'
# for the Probability component, and normalized 'cost' for the DrillCost
# component.
#
# Once trained, a full probability distribution can be theorized based on a
# gameplay field with a subset of sites surveyed, by the following algorithm.
#
#  - generate 50% overlapping regions (both directions) to cover whole field
#  - apply each such region to the backing autoassociative NN
#  - update each site in the field according to a weighted average from the NN
#      outputs for each region that overlaps it. (weights are based on number
#      of surveyed sites in the region)
#  - profit
class ProbabilityPrediction(Component):
    """Theorize a probability distribution"""
    name = 'probability'
    inputs = 30
    outputs = 30
    val_funcs = [OilProbability(theme, 30, normalize=True)]

    def theorize(self, field):
        pass


class DrillCostPrediction(Component):
    """Theorize a drill cost distribution"""
    name = 'drill_cost'
    inputs = 30
    outputs = 30

    def theorize(self, field):
        pass


class Agent:
    cmps = [Surveying, Report, Drilling, Sales, ProbabilityPrediction,
            DrillCostPrediction]

    @staticmethod
    def init(dir):
        return Agent(dir, dict([(c.name, c.init(dir)) for c in Agent.cmps]))

    @staticmethod
    def load(dir):
        return Agent(dir, dict([(c.name, c.load(dir)) for c in Agent.cmps]))

    def __init__(self, dir, comps):
        self.dir = dir
        self.comps = comps
        self.__dict__.update(comps)

    def save(self):
        map(lambda x: x.save(self.dir), self.comps.values())

    def learn(self):
        ## TODO play one billion games
        pass

    def play(self, hostname, port):
        ## TODO connect to a game a play mercilessly
        pass
