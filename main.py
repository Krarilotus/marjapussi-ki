import random
from marjapussi.game import MarjaPussi

if __name__ == '__main__':
    game = MarjaPussi(['Name1', 'Name2', 'Name3', 'Name4'])

    while not game.phase == "DONE":
        legal_actions = game.legal_actions()

        print(game.phase)
        print(legal_actions)

        print(game.players_cards())

        input()

        action = random.choice(legal_actions)
        game.act_action(action)
