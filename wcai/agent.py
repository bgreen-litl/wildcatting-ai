import os
import random
import numpy as np
import neurolab as nl

from os.path import join, exists

from wildcatting.theme import DefaultTheme

from .data import OilProbability, DrillCost, OilPresence, Region


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
                               [cls.inputs, hiddens, cls.outputs])
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

        self.nn.train(inp, out, epochs=500, show=10, goal=0.25)


class Surveying(Component):
    name = 'surveying'
    inputs = 60   # prob0, cost0 [..] probn, costn
    outputs = 30  # expected utilities of surveying each site
    val_funcs = [OilProbability(theme, 80 * 24, normalize=True),
                 DrillCost(theme, 80 * 24, normalize=True),
                 OilPresence(theme, 80 * 24, normalize=True)]

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
        outputs = self.nn.sim([inputs])[0]
        return Surveying.select_output(outputs)

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
        map = Region.map(region.field, Surveying.val_funcs, r.center,
                         (region.width / 2, region.height / 2))
        return self._choose(map, scale / 2)

    def choose(self, field):
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
