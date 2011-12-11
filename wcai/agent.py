import os
import random
import numpy as np
import neurolab as nl

from os.path import join, exists

from wildcatting.theme import DefaultTheme

from .data import OilProbability, Region


theme = DefaultTheme()


class Agent:
    @staticmethod
    def init(dir):
        agent = Agent(dir)
        agent.surveying = Surveying.init(dir)
        agent.report = Report.init(dir)
        agent.drilling = Drilling.init(dir)
        agent.sales = Sales.init(dir)
        return agent

    @staticmethod
    def load(dir):
        agent = Agent(dir)
        agent.surveying = Surveying.load(dir)
        agent.report = Surveying.load(dir)
        agent.drilling = Drilling.load(dir)
        agent.sales = Sales.load(dir)
        return agent

    def __init__(self, dir):
        self.dir = dir

    def save(self):
        self.surveying.save(self.dir)
        self.report.save(self.dir)
        self.drilling.save(self.dir)
        self.sales.save(self.dir)

    def learn(self):
        ## TODO play one billion games
        pass

    def play(self, hostname, port):
        ## TODO connect to a game a play mercilessly
        pass


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

    def train(self):
        inp = []
        out = []
        # TODO support numpy binary datafiles
        dir = join(self.dir, 'training')
        for tf in os.listdir(dir):
            data = np.loadtxt(join(dir, tf))
            for d in data:
                inp.append(d[:self.inputs])
                out.append(d[self.inputs:])
        self.nn.train(inp, out, epochs=50, show=1, goal=0.5)
        self.nn.save(join(self.dir, 'utility.net'))


class Surveying(Component):
    name = 'surveying'
    # TODO incorporate drill cost input and expected utility output
    inputs = 30  # prob
    outputs = 30  # reservoir size for now
    val_funcs = [OilProbability(theme, 80 * 24, normalize=True)]

    # Select the site to survey from a region of the correct size to apply
    # directly to the NN. Makes a choice with probabilities proportional to
    # the expected utility as estimated by the NN.
    def _choose_nn(self, region):
        inputs = region.inputs(['prob'])
        outputs = self.nn.sim([inputs])[0]
        tot_out = reduce(lambda x, y: x + y, outputs)
        r = random.uniform(0, 1)
        t = 0
        for i, o in enumerate(outputs):
            t += o / tot_out
            if r <= t:
                break
        return i

    # Choose a site to survey from the specified region of the field. The
    # region here is always at 1:1 but varies in size. The scale is the factor
    # by which the region must be reduced in order to apply the NN.
    def _choose(self, region, scale):
        if scale == 1:
            i = self._choose_nn(region)
            c = (i % region.width, i / region.height)
            x = region.center[0] - region.size[0] / 2 + c[0]
            y = region.center[1] - region.size[1] / 2 + c[1]
            return x, y

        r = Region.reduce(region, scale)
        i = self._choose_nn(r)
        map = Region.map(region.field, Surveying.val_funcs, r.center,
                         (region.width / 2, region.height / 2))
        return self._choose(map, scale / 2)

    def choose(self, field):
        """Choose a site to survey in the specified field"""
        map = Region.map(field, Surveying.val_funcs)
        coords = self._choose(map, 8)
        return coords


class Report(Component):
    name = 'report'
    inputs = 4   # prob, cost, tax
    outputs = 2  # expected utility of drilling and of not drilling


class Drilling(Component):
    name = 'drilling'
    inputs = 3   # cost, depth, expected depth
    outputs = 2  # expected utiltiy of drilling and of not drilling


class Sales(Component):
    name = 'sales'
    inputs = 3   # income, tax, age
    outputs = 2  # expected utility of selling and of not selling
