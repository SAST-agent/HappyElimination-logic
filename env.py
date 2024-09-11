import gym
import numpy as np
from gym import spaces
import json


class EliminationEnv(gym.Env):
    metadata = {'render_modes': ['saiblo', 'local']}

    def __init__(self, render_mode=None, size=20, categories=4, max_round = 100):
        self.size = size
        self.categories = categories
        self._last_elimination = []
        self._last_new = []
        self._last_operation = []
        self._round = 0
        self._max_round = max_round

        self.observation_space = spaces.MultiDiscrete(
            np.ones((size, size))*categories)
        
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

    def reset(self, seed=None, board=None):
        super().reset(seed=seed)
        
        if self._board is not None:
            self._board = board
        else:
            self._board = self.np_random.integers(
                0, self.categories, size=(self.size, self.size), dtype=int)
        self._round = 0
        
        self._last_new = [[]]
        self._last_elimination = [[]]
        
        if self.render_mode == 'saiblo':
            for i in range(self.size):
                for j in range(self.size):
                    self._last_new[0].append([i, j, int(self._board[i][j])])

    def step(self):
        pass

    def render(self):
        if self.render_mode == 'local':
            return self._board
        elif self.render_mode == 'saiblo':
            return_dict = {
                'round': self._round,
                'steps': self._max_round-self._round,
                'player': 0,
                'operation': self._last_operation,
                'elimination': self._last_elimination,
                'new': self._last_new
            }
            return json.dumps(return_dict, ensure_ascii=False)

    def observation_space(self):
        pass

    def action_space(self):
        pass


env = EliminationEnv(render_mode='saiblo')
env.reset(seed=45)
print(env.render())
