import numpy
from core.GymEnvironment import EliminationEnv

with open("replay.jsonl", "w") as fout:
    env = EliminationEnv(render_mode="logic")
    env.reset(seed=45)
    env.render()
    while 1:
        op = input()
        env.step([int(i) for i in op.split(" ")])
        env.render()

# env = EliminationEnv(render_mode="logic")
# env.reset(seed=45)
# env.render()
