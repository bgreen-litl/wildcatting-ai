import logging

from wildcatting.theme import DefaultTheme

from .data import Simulator, Region, OilProbability, DrillCost
from .agent import (Agent, Surveying, Report, Drilling, Sales,
                    ProbabilityPrediction, DrillCostPrediction)


log = logging.getLogger("wcai")

components = dict([(c.name, c) for c in [Surveying, Report, Drilling, Sales,
                                         ProbabilityPrediction,
                                         DrillCostPrediction]])


class InitCommand:

    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("init",
                                      help="initialize a wildcatting agent")
        subparser.add_argument("agent", help="agent name (dir to write to)")
        subparser.add_argument("--components", choices=components.keys(),
                               nargs='+',
                               help="only initialize specified components")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        if args.components:
            for comp in args.components:
                components[comp].init(args.agent)
        else:
            Agent.init(args.agent)


class TrainCommand:

    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("train",
                                      help=("bootstrap a component using "
                                            "supervised training data"))
        subparser.add_argument("agent", help="agent name (directory)")
        subparser.add_argument("component", choices=components.keys(),
                               help="component to train")
        subparser.add_argument("--epochs", default=100, type=int,
                               help="training epochs")
        subparser.add_argument("--show", default=10, type=int,
                               help="show error every n epochs")
        subparser.add_argument("--goal", default=0.1, type=float,
                               help="goal error rate")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        comp = components[args.component].load(args.agent)
        comp.train(args.epochs, args.show, args.goal)


class SimulateCommand:

    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("simulate",
                help=("simulate a component using generated game data"))
        subparser.add_argument("agent", help="agent name (directory)")
        subparser.add_argument("component", choices=components.keys(),
                               help="component to simulate")
        subparser.add_argument("--width", default=80, type=int,
                               help="oil field width")
        subparser.add_argument("--height", default=24, type=int,
                               help="oil field height")
        subparser.add_argument("--visualize", action='store_true',
                               default=False, help="output visualization aid")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        comp = components[args.component].load(args.agent)
        theme = DefaultTheme()
        sim = Simulator(theme)
        field = sim.field(args.width, args.height)
        site_ct = args.width * args.height
        vfs = [OilProbability(theme, site_ct=site_ct, normalize=True),
               DrillCost(theme, site_ct, True)]
        region = Region.map(field, val_funcs=vfs)
        if args.visualize:
            print region
        col, row = comp.choose(field)
        site = field.getSite(row, col)
        print (col, row), '->', site.getProbability(), site.getDrillCost()


class LearnCommand:

    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("learn",
                                      help="learn how to play wildcatting")
        subparser.add_argument("agent", help="agent name (directory)")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        agent = Agent.load(args.agent)
        agent.learn()


class PlayCommand:

    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("play",
                                      help="play wildcatting")
        subparser.add_argument("agent", help="agent name (directory)")
        subparser.add_argument("host", help="wildcatting server hostname")
        subparser.add_argument("game_id", help="game id")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        agent = Agent.load(args.agent)
        agent.play(args.host, args.game_id)
