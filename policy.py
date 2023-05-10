import math
import random as rnd
from prolog import Functor
from swiplserver import PrologMQI, PrologThread
from action import Action
from marjapussi.policy import Policy
import marjapussi.utils as putils
import string
from copy import deepcopy
from pprint import pprint


def _convert_prov_history_to_steps(p):
    p = [(-1, 115)] + p
    for i, pr in enumerate(p):
        if pr[1] == 0:
            p[i] = (p[i][0], p[i - 1][1])
    steps = [(n, j - i) for n, i, j in zip(list(zip(*p))[0][1:], list(zip(*p))[1][:-1], list(zip(*p))[1][1:])]
    steps_player_num = {playernum: [s for p, s in steps if p == playernum] for playernum in range(4)}
    return steps_player_num


def _action_string(state, action, value):
    return f'{state["player_num"]},{action},{value}'


def _card_deconstructor(card):
    color, value = card.lower().split('-')
    return color, value


def _is_card(card):
    return card in putils.CARDS


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
        self.has_card = Functor("has_card", 3)  # player_num, color, value
        self.has_not_card = Functor("has_not_card", 3)  # player_num, color, value

        self.q(self.assertz(self.prov_ace(-1)))
        self.q(self.assertz(self.prov_small_pair(-1)))
        self.q(self.assertz(self.prov_big_pair(-1)))
        self.q(self.assertz(self.prov_three_halves(-1)))
        self.q(self.assertz(self.has_pair(-1, 'col')))
        self.q(self.assertz(self.has_not_card(-1, 'col', 'l')))

        self.predicates = [
            self.prov_ace,
            self.prov_small_pair,
            self.prov_big_pair,
            self.prov_three_halves,
            self.has_pair
        ]

        self.prev_action = None
        self.prev_state = None

    """
    This method is called when the agent
    gets it's cards.
    """
    def start_hand(self, possible_cards) -> None:
        print(possible_cards)

    def _print_knowledge_base(self):
        for predicate in self.predicates:
            # print(predicate.arity == len(string.ascii_uppercase[:predicate.arity]))
            print(predicate.name, self.q(predicate(*string.ascii_uppercase[:predicate.arity])))

    def _update_provoking_beliefs(self, state, prev_state, legal_actions):

        # update beliefs for all players
        for player_num in range(4):
            partner_num = (player_num + 2) % 4
            steps = _convert_prov_history_to_steps(state['provoking_history'])

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
                    # if he did not prov an ace in the first step
                    # he does not have an ace
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

    # def _update_possible_card_beliefs(self, state, prev_state, legal_actions):
    #     # remove cards that were in the possible cards
    #     # but are not in the hand anymore
    #
    #     prev_possible_cards = prev_state['possible_cards']
    #     possible_cards = state['possible_cards']
    #
    #     # possible cards is a dict which has the player name as key
    #     # and a set of the possible cards as value
    #
    #     # TODO fertig stellen
    #     for i, hand in enumerate(possible_cards):
    #         now_impossible_cards = prev_possible_cards[i].difference(hand)
    #         for card in now_impossible_cards:
    #             color, value = _card_deconstructor(card)
    #             self.q(self.retract(self.has_card(i, color, value)))

    def observe_action(self, state, action) -> None:
        action = Action(*action.split(','))
        _prev_action = deepcopy(self.prev_action)
        self.prev_action = deepcopy(action)
        partner_num = (action.player_num + 2) % 4

        val = action.value
        player_num = action.player_num

        if action.phase == 'TRCK':
            if _is_card(action.value):
                current_card_color, current_card_value = _card_deconstructor(action.value)
            if state['current_trick'] and _is_card(state['current_trick'][0]):
                first_card_color, first_card_value = _card_deconstructor(state['current_trick'][0].split('-'))
                
            # # check whether a player in the first trick has to play green or an ace
            # if len(state['all_tricks']) == 0:
            #     if action.value.split('-')[1] != 'A':
            #         for i in putils.COLORS:
            #             self.q(self.assertz(self.has_not_card(player_num, i, 'A')))
            #     if action.value.split('-')[0] != 'g':
            #         for i in putils.VALUES:
            #             self.q(self.assertz(self.has_not_card(player_num, 'g', i)))

            # if a player can not serve a color, he does not have any card of that color
            if first_card_color != current_card_color:
                for i in putils.VALUES:
                    self.q(self.assertz(self.has_not_card(player_num, current_card_color, i)))

    def select_action(self, state, legal_actions) -> str:
        _prev_state = deepcopy(self.prev_state)
        self.prev_state = deepcopy(state)

        game_phase = legal_actions[0].split(',')[1]

        if game_phase == 'PROV':
            self._update_provoking_beliefs(state, _prev_state, legal_actions)
            self._print_knowledge_base()
            # if you have an ace (no matter what else you have)
            #   you can provoke +5
            # do not provoke 5 if your partner has an ace

            if not self.q(self.prov_ace(state['player_num'])) \
                    and not self.q(self.prov_ace((state['player_num'] + 2) % 4)):
                # do we have an ace?
                x = [card[-1] == "A" for card in state['cards']]
                if any(x):
                    self.q(self.assertz(self.prov_ace(state['player_num'])))
                    return _action_string(state, 'PROV', state['game_value'] + 5)
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
                                if state['game_value'] == 140:
                                    return _action_string(state, 'PROV', state['game_value'] + 20)
                                return _action_string(state, 'PROV', state['game_value'] + 15)
                            else:
                                return _action_string(state, 'PROV', state['game_value'] + 10)
                # do we have three halves?
                halves = [card for card in state['cards'] if card[-1] in "KO"]
                if len(halves) >= 3:
                    self.q(self.prov_three_halves(state['player_num']))
                    return _action_string(state, 'PROV', state['game_value'] + 10)

            return _action_string(state, 'PROV', 0)

        elif game_phase == 'TRCK':
            # self._update_possible_card_beliefs(state, _prev_state, legal_actions)
            print()

        return rnd.choice(legal_actions[:int(math.ceil(len(legal_actions) / 2))])
