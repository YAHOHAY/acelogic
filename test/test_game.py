from ace_logic.core.deck import Deck
from ace_logic.utils.evaluator import HandEvaluator


def test_game():
    """
    Simulates a 2-player Texas Hold'em showdown
    """
    print("===Welcome to Texas Hold'em showdown===")
    #1.Initialzation
    deck = Deck()
    deck.shuffle()

    #2.Dealing Card4 Each player gets 2 hole Cards
    player_a_hole = deck.deal(2)
    player_b_hole = deck.deal(2)

    #5 community cards on the table
    community_cards = deck.deal(5)

    print(f"\n[Community Cards]: {community_cards}")
    print(f"[Player A Hole]: {player_a_hole}")
    print(f"[Player B Hole]: {player_b_hole}")
    #3.Form 7-Card pools
    pool_a = player_a_hole + community_cards
    pool_b = player_b_hole + community_cards
    #4.Find the best 5-Card hang for each player
    best_a, score_a = HandEvaluator.get_best_hand(pool_a)
    best_b, score_b = HandEvaluator.get_best_hand(pool_b)

    #5.showdown and result
    print(f"Player A's Best Hand: {best_a} -> {HandEvaluator.evaluate_to_str(score_a[0])}")
    print(f"Player B's Best Hand: {best_b} -> {HandEvaluator.evaluate_to_str(score_b[0])}")
    if score_a > score_b:
        print("\n🏆 RESULT: Player A WINS!")
    elif score_a < score_b:
        print("\n🏆 RESULT: Player B WINS!")
    else:
        print("\n🤝 RESULT: It's a TIE (Split Pot)!")