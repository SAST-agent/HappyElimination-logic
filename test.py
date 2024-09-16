import random

from core.GymEnvironment import EliminationEnv

env = EliminationEnv(render_mode='logic')
env.reset()

while (1):
    env.step([random.randint(0, 19) for i in range(4)], player=0)
    print(env.render())
    env.step([random.randint(0, 19) for i in range(4)], player=1)
    print(env.render())
