# Marjapussi Formalisierung

## Reizen
- unter 140
  - falls noch kein Ass in der Partei angesagt wurde und man ein Ass hat, Ass ansagen (+5)
  - sonst erst große Paare (+15), dann kleine Paare (+10), dann 3 Hälften (+10) (wenn die Mit- und Gegenspieler höher gehen gern alles ansagen)

- über 140
  - auch +15 für große Paare
  - wenn man 3 Hälften hat nicht über 140 gehen, außer der Mitspieler hat mindestens +10 gesagt (3 Hälften oder ein kleines Paar), denn dann hat die Partei definitiv die Chance das Spiel zu gewinnen. Wenn es 3 Hälften sind, hat man definitiv 2 Paare sicher.   
  - wenn man 2 Hälften hat und der Mitspieler +10 gesagt hat

```prolog

game_value(140).

%Mitspieler sagt erstmalig +5 an
assertz(has_ace(1, 0.9)). 

%Ein Gegenspieler sagt erstmalig +5 an
assertz(has_ace(2, 0.9)). %Gegner sagt +5 an

%Mitspieler sagt +10 oder geht über 140
%wir sind unter 140
assertz(has_small_pair(1, 0.7))
assertz(has_three_halves(1, 0.3))

%über 140
assertz(has_small_pair(1, 0.9))

```