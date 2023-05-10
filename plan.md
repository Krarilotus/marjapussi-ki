# Plan

## Changes to Framework
DONE: possible cards does not check whether player played green as first card
+ fix possible issues with the possible cards in general (check for bugs)
+ standing cards: add whole function
+ winrate observation and testing
+ redo backend to reduce pain with string operations (class and property based obejcts!)

## Changes to the very smart policy
+ rules for picking cards in every turn, implementing basic 'good fallback' traits, if no other specific move is deemed 'very good'
+ check if you will win the next trick
+ standing cards
  + check which cards will be standing (e.g. A, 10, K, O, 7. 7 is standing after A, 10, K, O is played.)
