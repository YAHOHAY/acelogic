from ace_logic.core.card import Card, Suit, Rank
def test_suit_init():
    c1 = Card(Suit.SPADES, Rank.ACE)
    c2 = Card(Suit.HEARTS, Rank.TEN)
    assert c1 > c2
