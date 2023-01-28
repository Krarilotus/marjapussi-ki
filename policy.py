import math
import random as rnd
from pprint import pprint
import pytholog as pl

from marjapussi.policy import Policy
import marjapussi.utils as putils


class VerySmartPolicy(Policy):

    def __init__(self) -> None:
        super().__init__()
        self.beliefs = {}
        self.knowledge = {}

        self.knowledge_base = pl.KnowledgeBase("pussi")

        """
            knowledge base
            has_ace(PlayerNum, prob)
            has_no_ace(PlayerNum, prob)
        """
        self.knowledge_base([
            # initialise knowledge base (like production rules)
        ])

    def _action_string(self, state, action, value):
        return f'{state["player_num"]},{action},{value}'

    def _convert_prov_history_to_steps(self, p):
        p = [(-1, 115)] + p
        for i, pr in enumerate(p):
            if pr[1] == 0:
                p[i] = (p[i][0], p[i - 1][1])
        steps = [(n, j - i) for n, i, j in zip(list(zip(*p))[0][1:], list(zip(*p))[1][:-1], list(zip(*p))[1][1:])]
        steps_player_num = {playernum: [s for p, s in steps if p == playernum] for playernum in range(4)}
        return steps_player_num

    def _update_provoking_beliefs(self, state, legal_actions):
        # does partner have an ace?

        steps = self._convert_prov_history_to_steps(state['provoking_history'])

        # only update things we do not know yet
        if self.knowledge_base.query(f"has_ace({(state['player_num'] + 2) % 4})"):

        # only update if we don't know yet
        # and if we have seen the partner's first step
        # and if any of our steps is not 5
        if 'partner_has_ace' not in self.beliefs \
                and steps[(state['player_num'] + 2) % 4] \
                and not self.knowledge.get('prov_ace'):
            if steps[(state['player_num'] + 2) % 4][0] == 5:
                print("PARTNER HAS AN ACE")
                self.knowledge_base([f"has_ace({state['player_num'] + 2})"])
                self.beliefs['partner_has_ace'] = 1
            else:
                self.knowledge_base([f"has_no_ace({state['player_num'] + 2})"])
                self.beliefs['partner_has_ace'] = 0

        if 'partner_has_a_small_pair' not in self.beliefs:
            if 10 in steps[(state['player_num'] + 2) % 4]:
                if state['game_value'] < 140:
                    print("PARTNER HAS MAYBE A SMALL PAIR OR THREE HALVES")
                    self.knowledge_base([f"has_small_pair({state['player_num'] + 2}, 0.5)"])
                    self.knowledge_base([f"has_three_halves({state['player_num'] + 2}, 0.5)"])
                    self.beliefs['partner_has_a_small_pair'] = 0.5
                    self.beliefs['partner_has_three_halves'] = 0.5
                else:
                    print("PARTNER HAS VERY PROBABLY SMALL PAIR")
                    self.beliefs['partner_has_a_small_pair'] = 1

        if 'partner_has_a_big_pair' not in self.beliefs:
            if 15 in steps[(state['player_num'] + 2) % 4]:
                print("PARTNER HAS A SMALL PAIR")
                self.beliefs['partner_has_a_big_pair'] = 1

    def select_action(self, state, legal_actions) -> str:
        # pprint(state)
        # print(legal_actions)

        game_phase = legal_actions[0].split(',')[1]

        pprint(self.beliefs)

        if game_phase == 'PROV':
            self._update_provoking_beliefs(state, legal_actions)
            # if you have an ace (no matter what else you have)
            #  you can provoke +5
            # do not provoke 5 if your partner has an ace

            if not self.knowledge.get("prov_ace") and not self.beliefs.get('partner_has_ace', False):
                # do we have an ace?
                x = [card[-1] == "A" for card in state['cards']]
                if any(x):
                    self.knowledge["prov_ace"] = True
                    return self._action_string(state, 'PROV', state['game_value']+5)
            else:
                # do we have pairs?
                for color in putils.COLORS:
                    # go through all colors
                    if putils.contains_pair(state['cards'], color):
                        if not self.knowledge.get(f"prov_pair_{color}"):
                            self.knowledge['prov_pair_' + color] = True
                            if color in "rs":
                                return self._action_string(state, 'PROV', state['game_value'] + 15)
                            else:
                                return self._action_string(state, 'PROV', state['game_value'] + 10)
                # do we have three halves?
                halves = [card for card in state['cards'] if card[-1] in "KO"]
                if len(halves) >= 3:
                    return self._action_string(state, 'PROV', state['game_value'] + 10)

            return self._action_string(state, 'PROV', 0)

        return rnd.choice(legal_actions[:int(math.ceil(len(legal_actions)/2))])