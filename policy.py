import math
import random as rnd
from prolog import Functor
from swiplserver import PrologMQI, PrologThread

from marjapussi.policy import Policy
import marjapussi.utils as putils
import string


class VerySmartPolicy(Policy):

    def __init__(self) -> None:
        super().__init__()
        self.mqi = PrologMQI()
        self.prolog_thread = self.mqi.create_thread()

        self.q = self.prolog_thread.query

        # assert as last statement of the predicate
        self.assertz = Functor("assertz", 1)

        # assert as first statement of the predicate
        self.asserta = Functor("asserta", 1)

        # retract all facts from the database
        self.retract = Functor("retract", 1)

        # our predicates
        self.prov_ace = Functor("prov_ace", 1)  # player_num
        self.prov_small_pair = Functor("prov_small_pair", 1)  # player_num
        self.prov_big_pair = Functor("prov_big_pair", 1)  # player_num
        self.prov_three_halves = Functor("prov_three_halves", 1)  # player_num
        self.has_pair = Functor("has_pair", 2)  # player_num, color

        self.q(self.assertz(self.prov_ace(-1)))
        self.q(self.assertz(self.prov_small_pair(-1)))
        self.q(self.assertz(self.prov_big_pair(-1)))
        self.q(self.assertz(self.prov_three_halves(-1)))
        self.q(self.assertz(self.has_pair(-1, 'col')))

        self.predicates = [
            self.prov_ace,
            self.prov_small_pair,
            self.prov_big_pair,
            self.prov_three_halves,
            self.has_pair
        ]

    def _print_knowledge_base(self):
        for predicate in self.predicates:
            # print(predicate.arity == len(string.ascii_uppercase[:predicate.arity]))
            print(predicate.name, self.q(predicate(*string.ascii_uppercase[:predicate.arity])))

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

        # update beliefs for all players
        for player_num in range(4):
            partner_num = (player_num + 2) % 4
            steps = self._convert_prov_history_to_steps(state['provoking_history'])

            # only update things we do not know yet
            # if self.knowledge_base.query(f"prov_ace({(state['player_num'] + 2) % 4})"):

            # only update if we don't know yet
            # and if we have seen the partner's first step
            # and if any of our steps is not 5
            if self.q(self.prov_ace(partner_num)) \
                    and steps[partner_num] \
                    and not self.q(self.prov_ace('X')):
                if steps[partner_num][0] == 5:
                    print("player " + str(partner_num) + " has an ace")
                    self.q(self.prov_ace(partner_num))
                else:
                    print("player " + str(partner_num) + " does not have an ace")
                    self.q(self.prov_ace(partner_num))

            # if the partner has not told us about his small pair yet
            if not self.q(self.prov_small_pair(partner_num)):
                if 10 in steps[partner_num]:
                    if state['game_value'] < 140:
                        self.q(self.assertz(self.prov_small_pair(partner_num)))
                        self.q(self.assertz(self.prov_three_halves(partner_num)))
                    else:
                        self.q(self.assertz(self.prov_big_pair(partner_num)))

            # if the partner has not told us about his big pair yet
            if not self.q(self.prov_big_pair(partner_num)):
                if 15 in steps[partner_num]:
                    self.q(self.assertz(self.prov_big_pair(partner_num)))

    def select_action(self, state, legal_actions) -> str:
        game_phase = legal_actions[0].split(',')[1]

        if game_phase == 'PROV':
            self._update_provoking_beliefs(state, legal_actions)
            self._print_knowledge_base()
            # if you have an ace (no matter what else you have)
            #  you can provoke +5
            # do not provoke 5 if your partner has an ace

            if not self.q(self.prov_ace(state['player_num'])) \
                    and not self.q(self.prov_ace((state['player_num'] + 2) % 4)):
                # do we have an ace?
                x = [card[-1] == "A" for card in state['cards']]
                if any(x):
                    self.q(self.assertz(self.prov_ace(state['player_num'])))
                    return self._action_string(state, 'PROV', state['game_value'] + 5)
            else:
                # do we have pairs?
                for color in putils.COLORS:
                    # go through all colors
                    if putils.contains_pair(state['cards'], color):
                        # if we have a pair of this color
                        if not self.q(self.has_pair(state['player_num'], color)):
                            # if we have not provoked this pair yet
                            # memorize that we did and do that now
                            self.q(self.assertz(self.has_pair(state['player_num'], color)))
                            if color in "rs":
                                return self._action_string(state, 'PROV', state['game_value'] + 15)
                            else:
                                return self._action_string(state, 'PROV', state['game_value'] + 10)
                # do we have three halves?
                halves = [card for card in state['cards'] if card[-1] in "KO"]
                if len(halves) >= 3:
                    self.q(self.prov_three_halves(state['player_num']))
                    return self._action_string(state, 'PROV', state['game_value'] + 10)

            return self._action_string(state, 'PROV', 0)

        return rnd.choice(legal_actions[:int(math.ceil(len(legal_actions) / 2))])
