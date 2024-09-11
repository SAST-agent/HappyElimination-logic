import numpy as np
from gym import spaces

observation_space = spaces.MultiDiscrete(np.ones((10, 10))*4)
print(type(observation_space.sample()))
