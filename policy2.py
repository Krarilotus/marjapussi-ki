import math
import random as rnd
from pprint import pprint

from marjapussi.policy import Policy


class AlwaysProvokePolicy(Policy):

    def __init__(self) -> None:
        super().__init__()
        self.beliefs = {}

    def _action_string(self, state, action, value):
        return f'{state["player_num"]},{action},{value}'

    def select_action(self, state, legal_actions) -> str:
        game_phase = legal_actions[0].split(',')[1] == 'PROV'

        if game_phase == 'PROV':
            # if you have an ace (no matter what else you have)
            #  you can provoke +5
            # do not provoke 5 if your partner has an ace
            return self._action_string(state, 'PROV', state['game_value']+5)

        return rnd.choice(legal_actions[:int(math.ceil(len(legal_actions)/2))])