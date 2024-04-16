import numpy as np
from gym import Env
from gym.spaces import Box, Discrete
import copy


class TicTacToeEnv(Env):
    """
    ### Description

    This is an environment for playing Tic Tac Toe (or Noughts and Crosses).
    Each player takes it in turn to mark a position in a square grid (e.g., 3x3), until they form a horizontal, vertical or diagonal
    line across the grid (e.g., 3 in a row), in which case they win. If no further moves can be made and there is no winner
    then the game is a draw.

    ### Action Space

    The action is an `integer` which can take values {0, 1, ..., (n ** 2) - 1}, where n is the size of the grid, starting at 
    [0, 0], which is action 0, then on to [0, 1] which is action 1, and moving through row by row, until action (n ** 2) - 1, 
    which is [n - 1, n - 1].

    ### Observation Space

    The observation is a `ndarray` with shape `(n, n)`, where n is the grid size. Each entry can take the following values:

    | Value | Meaning                                |
    |-------|----------------------------------------|
    | 0     | No mark here yet, free to mark         |
    | 1     | Player 1 has placed a mark here        |
    | -1    | Player 2 has placed a mark here        |
    
    ### Rewards

    A reward of +1 is given to the winning player with a reward of -1 for the losing player.
    If it's a draw both players get a reward of 0.

    ### Starting State

    (n, n) grid of zeros.

    ### Episode End

    The episode ends if any one of the following occurs:
    1. Termination: A player gets n successive marks in a row, column or diagonal for an (n, n) grid.
    2. Termination: No more moves can be played (i.e., every grid position is marked).

    ### Arguments

    ```
    gym.make('tictactoe-gui-v0')
    ```

    No additional arguments are currently supported.

    Attributes
    ----------
    size : int
        The size of the grid.
    
    observation_space : gym.spaces.Box
        The observation space, an (n, n) grid.

    action_space : gym.spaces.Discrete
        The action space, an (n**2 - 1) list.

    reward_range : int
        The reward range, -1 for a loss, 0 for a draw, +1 for a win.

    _player : int
        The current player, 1/-1.

    _state_size : tuple
        A (1, 3) tuple of the state size - (size, size, 1).

    _action_to_index_map : dict
        A mapping from actions to indices, e.g., {0: [0, 0], 1: [0, 1], 2: [0, 2], 3: [1, 0], ..., 8: [2, 2]}.

    _history : list
        The history of actions, e.g., [0, 5, 1, 3, 2].

    _terminal : bool
        Whether the game is finished or not.

    _winner : int
        The winning player, 1 for player 1, -1 for player 2 and 0 for a draw.

    """

    def __init__(self, size=3):
        """
        The __init__ method. Initialises environment and all attributes.

        Parameters
        ----------
        size : int
            The size of the grid in the game.

        """

        self.size = size
        self.observation_space = Box(low=-1, high=1, shape=(self.size, self.size), dtype=np.int64)
        self.action_space = Discrete(self.size ** 2)
        self.reward_range = (-1, 1)

        self._player = 1
        self._state_size = (self.size, self.size, 1)
        self._action_to_index_map = self._get_action_to_index_map()
        self._history = []
        self._terminal = False
        self._winner = 0

    def get_observation(self, player):
        """
        Gets observation for a player.

        Parameters
        ----------
        player : int
            Either 1 for player 1's observation of -1 for player 2's observation.

        Returns
        -------
        ndarray
            The players observation (1 represents own marks, -1 represents oppositions marks and 0 represents free spaces).

        """

        if player == 1:
            return self._obs
        elif player == -1:
            # Flip all signs around for opposing player
            return -self._obs

    def get_actions(self):
        """
        Get possible actions, i.e., positions where marks have not yet been made.

        Returns
        -------
        list
            A list of possible actions (as integers), e.g., [0, 1, 7].

        """

        return [i for i in range(self.action_space.n) if self._obs[self._action_to_index_map[i]] == 0]

    def get_result(self, player):
        """
        Get result for a player.
        If the player is 1/-1 and winner is 1/-1, then return 1, as the requested player has won.
        Otherwise if the player is 1/-1 and winner is -1/1, then return -1, as the player has lost.
        If a draw, then self._winner is 0, so returns 0.

        Parameters
        ----------
        player : int
            Either 1 for player 1's result of -1 for player 2's result.

        Returns
        -------
        int
            The players result (1 represents a win, -1 represents a loss and 0 represents a draw).
        
        """

        return self._winner * player

    def _get_action_to_index_map(self):
        """
        Returns the action_to_index_map. This is more efficient as it saves having to compute indices every time.

        Returns
        -------
        dict
            A mapping from actions to indices, e.g., {0: [0, 0], 1: [0, 1], 2: [0, 2], 3: [1, 0], ..., 8: [2, 2]}.
        
        """

        action_index_map = {}
        for i in range(self.action_space.n):
            action_index_map[i] = (i // self.size, i % self.size)
        return action_index_map

    def _is_valid_action(self, action):
        """
        Checks an action is valid.

        Parameters
        ----------
        action : int
            The action to check validity of.

        Returns
        -------
        bool
            True if action is valid, False otherwise.
        
        """
        
        if self._obs[self._action_to_index_map[action]] == 0:
            return True
        else:
            return False

    def _row_winner(self, obs):
        """Returns winner of any row from an observation"""

        for row in obs:
            row_sum = sum(row)
            if abs(row_sum) == self.size:
                return row_sum / self.size
        return 0

    def _col_winner(self, obs):
        """Returns winner of any column from an observation"""

        obs_transpose = obs.T
        return self._row_winner(obs_transpose)

    def _main_diag_winner(self, obs):
        """Returns winner of main diagonal from an observation"""

        main_diag_sum = np.trace(obs)
        if abs(main_diag_sum) == self.size:
            return main_diag_sum / self.size
        return 0

    def _reverse_main_diag_winner(self, obs):
        """Returns winner of reverse main diagonal from an observation"""

        obs_flipped = obs[::-1]
        return self._main_diag_winner(obs_flipped)

    def _is_game_over(self):
        """
        Returns true if game is over and false otherwise. Also sets the winning player as the _winner or 0 for draw.

        Returns
        -------
        bool
            True if game is over, False otherwise.
        
        """

        # If all positions taken - then game over as no where to move.
        if len(self._history) == self.action_space.n:
            self._winner = 0
            return True
        
        # Complete line in any row
        winner = self._row_winner(self._obs)
        if winner != 0:
            self._winner = winner
            return True
        
        # Complete line in any column
        winner = self._col_winner(self._obs)
        if winner != 0:
            self._winner = winner
            return True

        # Complete line in main diagonal
        winner = self._main_diag_winner(self._obs)
        if winner != 0:
            self._winner = winner
            return True

        # Complete line in reverse diagonal
        winner = self._reverse_main_diag_winner(self._obs)
        if winner != 0:
            self._winner = winner
            return True

        return False

    def _get_info(self):
        """
        Get information on the game.

        Returns
        -------
        info : dict
            The game history, current player and winner.
        
        """

        return {"history": self._history, "player": self._player, "winner": self._winner}

    def step(self, action):
        """
        Step game using action and returns new observation, winner, game over indicator, truncated (always False here) and info.

        Parameters
        ----------
        action : int
            The action to check validity of.

        Returns
        -------
        ndarray
            The player's observation (1 represents own marks, -1 represents oppositions marks and 0 represents free spaces).

        int
            The winner of the game, +1 for player 1, -1 for player 2 and 0 for a draw.

        bool
            The game over indicator, True if the game is over, False otherwise.

        bool
            Always False. From gym api for whether a truncation condition is satisfied, e.g., agent out of bounds. Not used here.

        dict
            Game information, including the game history, current player and winner.
        
        """

        if not self._is_valid_action(action):
            print('Error: invalid action, please try again')            
            return self._obs, self._winner, self._terminal, False, self._get_info()
        else:
            self._obs[self._action_to_index_map[action]] = self._player
            self._history.append(action)

            # Check game over
            self._terminal = self._is_game_over()
            if not self._terminal:
                self._player *= -1   # Change player
            
            return self._obs, self._winner, self._terminal, False, self._get_info()

    def reset(self, seed=None, options=None):
        """
        Reset the game.

        Parameters
        ----------
        seed : int
            The random seed.

        options : dict
            Information on how the environment is to be reset. Not used here.

        Returns
        -------
        ndarray
            The initial observation, grid of all zeros.

        dict
            Game information, including the game history, current player and winner.
        
        """

        super().reset(seed=seed)

        self._obs = np.zeros((self.size, self.size), dtype=np.int64)
        self._history = []
        self._terminal = False
        self._winner = 0
        self._player = 1

        return self._obs, self._get_info()

    def clone(self):
        """
        Clone the game.

        Returns
        -------
        gym.Env
            A clone of the gym environment.

        """

        return copy.deepcopy(self)

    def render(self):
        """
        Renders the current observation in the terminal as a string.

        """
import gym
import numpy as np
import pygame
from gym.spaces import Discrete, Box
from gym.utils import EzPickle
from typing import Any, Tuple, Dict

class TicTacToeEnv(gym.Env, EzPickle):
    def __init__(self):
        super().__init__()
        self.action_space = Discrete(9)
        self.observation_space = Box(low=-1, high=1, shape=(9,), dtype=np.int8)
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.done = False
        self.winner = None

        # Initialize Pygame
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()

        # Load images
        self.cross_img = pygame.image.load("Cross.png")
        self.cross_img = pygame.transform.scale(self.cross_img, (100, 100))
        self.nought_img = pygame.image.load("Nought.png")
        self.nought_img = pygame.transform.scale(self.nought_img, (100, 100))

        # Initialize font
        self.font = pygame.font.SysFont("Arial", 32)

        EzPickle.__init__(self)

    def step(self, action: int) -> Tuple[np.ndarray, int, bool, Dict[str, Any]]:
        if self.done:
            raise RuntimeError("Episode is done, please reset the environment.")

        row, col = action // 3, action % 3
        if self.board[row][col] == ' ':
            print(f"Marked position: ({row}, {col})")
            self.board[row][col] = self.current_player
            self.winner = self._game_state(self.board)
            self.done = self.winner != 'ONGOING'
            reward = self._assign_reward(self.winner)
            if self.winner.endswith('_WON'):
                print(f"Congratulations! Player {self.current_player} won.")
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            observation = self._take_photo(self.board)
            return observation, reward, self.done, {}
        else:
            return self._get_observation(), 0, False, {}

    def _get_observation(self) -> np.ndarray:
        return self._take_photo(self.board)

    def reset(self) -> np.ndarray:
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.done = False
        self.winner = None
        return self._get_observation()

    def render(self):
        self.screen.fill((255, 255, 255))

        for row in range(3):
            for col in range(3):
                x_pos = col * 200 + 250
                y_pos = row * 200 + 150
                if self.board[row][col] == 'X':
                    self.screen.blit(self.cross_img, (x_pos, y_pos))
                elif self.board[row][col] == 'O':
                    self.screen.blit(self.nought_img, (x_pos, y_pos))
                pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(x_pos, y_pos, 100, 100), 1)

        pygame.display.flip()

    def _take_photo(self, board: list[list[str]]) -> np.ndarray:
        """Take a photo of the current board state."""
        return np.array(board).reshape(-1)

    def _game_state(self, board: list[list[str]]) -> str:
        """Determine the state of the game: ongoing, X won, O won, or draw."""
        lines = board + \
                [[board[j][i] for j in range(3)] for i in range(3)] + \
                [[board[i][i] for i in range(3)]] + \
                [[board[i][2 - i] for i in range(3)]]
        for line in lines:
            if len(set(line)) == 1 and line[0] != ' ':
                return line[0] + '_WON'
        if any(' ' in line for line in board):
            return 'ONGOING'
        return 'DRAW'

    def _assign_reward(self, state: str) -> int:
        """Assign reward based on the game state."""
        if state == 'X_WON':
            return 1
        elif state == 'O_WON':
            return -1
        else:
            return 0


def main():
    env = TicTacToeEnv()
    done = False
    observation = env.reset()
    env.render()

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                row = (mouse_y - 150) // 200
                col = (mouse_x - 250) // 200
                action = row * 3 + col
                observation, reward, done, info = env.step(action)
                env.render()

    pygame.quit()


if __name__ == "__main__":
    main()

