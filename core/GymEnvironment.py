import json

import gym
import numpy as np
from gym import spaces


class EliminationEnv(gym.Env):
    metadata = {"render_modes": ["local", "logic", "ai"]}

    def __init__(
        self,
        render_mode=None,
        size=20,
        categories=5,
        max_round=100,
        player=0,
        compete=True,
    ):
        assert size >= 3
        self.size = size
        self.categories = categories
        self._last_elimination = []
        self._last_new = []
        self._last_operation = []
        self._round = 0
        self._max_round = max_round
        self._board = None
        self._score = [0, 0]
        self._player = player
        self._compete = compete

        self.observation_space = spaces.MultiDiscrete(
            np.ones((size, size)) * categories
        )

        self.action_space = spaces.Discrete(size**4)

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

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
                    elif self._board[i][j] == 4:
                        print("\033[1;47m  \033[0m", end="")
        elif self.render_mode == 'logic':
            return_dict = {
                "round": self._round - 1,
                "steps": self._max_round - self._round + 1,
                "player": self._player,
                "operation": self._last_operation,
                "score": self._score,
                "ManyTimesEliminateBlocks": self._last_elimination,
                "ManyTimesNewBlocks": self._last_new,
                "StopReason": None,
            }
            return return_dict

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

    def _get_info(self):
        return {"score": self._score}

    def reset(self, seed=None, board=None):
        super().reset(seed=seed)

        self._round = 0
        self._last_new = [[]]
        self._last_elimination = [[]]
        self._last_operation = [[-1, -1], [-1, -1]]
        self._score = [0, 0]
        self._player = 0

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
            self._last_elimination = [[[]]]

        return self._board, self._get_info()

    def step(self, action, player=0):
        self._last_elimination = []
        self._last_new = []
        self._player = player

        d = action % 20
        c = int(((action - d) / 20) % 20)
        b = int(((action - c * 20 - d) / 400) % 20)
        a = int(((action - d - c * 20 - b * 400) / 8000) % 20)

        self._last_operation = [[a, b], [c, d]]
        self._board[a][b], self._board[c][d] = self._board[c][d], self._board[a][b]

        reward = 0
        while eliminated_set := self._eliminate_step(self._board):

            eliminated_map = np.zeros((20, 20), dtype=np.int32)
            # print(eliminated_set)
            reward += len(list(eliminated_set))
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

            new_map = new_board == -1
            new_board = np.where(new_map, new, new_board)

            eliminated = [
                [int(i / self.size), int(i % self.size)] for i in eliminated_set
            ]
            new = []
            for i in range(self.size):
                for j in range(self.size):
                    if new_map[i][j]:
                        new.append([i, j, int(new_board[i][j])])

            self._last_elimination.append(eliminated)
            self._last_new.append(new)

            self._board = new_board

        self._score[player] += reward

        if self._compete:
            if player == 0:
                self._round += 1
        else:
            self._round += 1

        return (self._board, reward, self._round == self._max_round)

    def observation_space(self):
        return self.observation_space

    def action_space(self):
        return self.action_space

    def num_to_coord(self, action):
        assert action >= 0 and action <= self.size**4
        d = action % 20
        c = int(((action - d) / 20) % 20)
        b = int(((action - c * 20 - d) / 400) % 20)
        a = int(((action - d - c * 20 - b * 400) / 8000) % 20)
        return [a, b, c, d]

    def coord_to_num(self, action):
        assert (
            action[0] >= 0
            and action[0] < self.size
            and action[1] >= 0
            and action[1] < self.size
            and action[2] >= 0
            and action[2] < self.size
            and action[3] >= 0
            and action[3] < self.size
        )
        return action[0] * 8000 + action[1] * 400 + action[2] * 20 + action[3]
