import numpy
from core.GymEnvironment import EliminationEnv

env = EliminationEnv(render_mode="local")
env.reset(seed=45)
env.render()

env = EliminationEnv(render_mode="logic")
env.reset(seed=45)
env.render()
