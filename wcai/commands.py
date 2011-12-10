import logging

from .agent import Agent, Surveying, Report, Drilling, Sales


log = logging.getLogger("wcai")

components = dict([(c.name, c) for c in [Surveying, Report, Drilling, Sales]])


class InitCommand:

    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser("init",
                                      help="initialize a wildcatting agent")
        subparser.add_argument("agent", help="agent name (dir to write to)")

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
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

        subparser.set_defaults(run=cls.run)

    @staticmethod
    def run(args):
        comp = components[args.component].load(args.agent)
        comp.train()


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
