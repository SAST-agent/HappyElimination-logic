import json

import gym
import numpy as np
from gym import spaces


class EliminationEnv(gym.Env):
    metadata = {"render_modes": ["local", "logic", "ai"]}

    def __init__(self, render_mode=None, size=20, categories=4, max_round=100):
        assert size >= 3
        self.size = size
        self.categories = categories
        self._last_elimination = []
        self._last_new = []
        self._last_operation = []
        self._round = 0
        self._max_round = max_round
        self._board = None

        self.observation_space = spaces.MultiDiscrete(
            np.ones((size, size)) * categories
        )

        self.action_space = spaces.Discrete(
            4 * 3 * (size - 2) + 8 + (size - 2) * (size - 2) * 4
        )

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

    def _communication(self):
        if self.render_mode == "logic":
            return_dict = {
                "round": self._round,
                "steps": self._max_round - self._round,
                "player": 0,
                "operation": self._last_operation,
                "ManyTimesEliminateBlocks": self._last_elimination,
                "ManyTimesNewBlocks": self._last_new,
            }
            print(
                f"communication with judger, content:{json.dumps(return_dict, ensure_ascii=False)}"
            )

    def render(self):
        if self.render_mode == "local":
            for i in range(self.size):
                print("")
                for j in range(self.size):
                    if self._board[i][j] == 0:
                        print("\033[1;41m  \033[0m", end="")
                    elif self._board[i][j] == 1:
                        print("\033[1;43m  \033[0m", end="")
                    elif self._board[i][j] == 2:
                        print("\033[1;44m  \033[0m", end="")
                    elif self._board[i][j] == 3:
                        print("\033[1;42m  \033[0m", end="")
            print("")

    def _eliminate_step(self, board):
        eliminated_position = set()
        for i in range(board.shape[0]):
            for j in range(2, board.shape[1]):
                if board[i][j] == board[i][j - 1] and board[i][j] == board[i][j - 2]:
                    eliminated_position.add(i * board.shape[1] + j)
                    eliminated_position.add(i * board.shape[1] + j - 1)
                    eliminated_position.add(i * board.shape[1] + j - 2)

        for i in range(2, board.shape[0]):
            for j in range(board.shape[1]):
                if board[i][j] == board[i - 1][j] and board[i][j] == board[i - 2][j]:
                    eliminated_position.add(i * board.shape[1] + j)
                    eliminated_position.add((i - 1) * board.shape[1] + j)
                    eliminated_position.add((i - 2) * board.shape[1] + j)

        return eliminated_position

    def reset(self, seed=None, board=None):
        super().reset(seed=seed)

        self._round = 0
        self._last_new = [[]]
        self._last_elimination = [[]]
        self._last_operation = [-1, -1, -1, -1]

        if board is not None:
            self._board = board
        else:
            self._board = self.np_random.integers(
                0, self.categories, size=(self.size, self.size), dtype=int
            )

            while eliminated_set := self._eliminate_step(self._board):

                eliminated_map = np.zeros((20, 20), dtype=np.int32)
                for i in eliminated_set:
                    eliminated_map[int(i / 20)][i % 20] = 1

                new_board = np.zeros_like(eliminated_map) - 1
                for j in range(20):
                    newi = 19
                    for orgi in reversed(range(20)):
                        if eliminated_map[orgi][j] == 0:
                            new_board[newi][j] = self._board[orgi][j]
                            newi -= 1

                new = self.np_random.integers(
                    0, self.categories, size=(self.size, self.size), dtype=int
                )
                new_board = np.where(new_board == -1, new, new_board)

                self._board = new_board

        if self.render_mode == "logic":
            for i in range(self.size):
                for j in range(self.size):
                    self._last_new[0].append([i, j, int(self._board[i][j])])
            self._communication()

    def step(self, action):
        self._last_elimination = []
        self._last_new = []
        self._last_operation = []
        while eliminated_set := self._eliminate_step(self._board):

            eliminated_map = np.zeros((20, 20), dtype=np.int32)
            for i in eliminated_set:
                eliminated_map[int(i / 20)][i % 20] = 1

            new_board = np.zeros_like(eliminated_map) - 1
            for j in range(20):
                newi = 19
                for orgi in reversed(range(20)):
                    if eliminated_map[orgi][j] == 0:
                        new_board[newi][j] = self._board[orgi][j]
                        newi -= 1

            new = self.np_random.integers(
                0, self.categories, size=(self.size, self.size), dtype=int
            )
            new_board = np.where(new_board == -1, new, new_board)

            self._board = new_board

        round += 1
        self._communication()

    def observation_space(self):
        pass

    def action_space(self):
        pass
