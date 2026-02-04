from ace_logic.core.card import Card, Suit, Rank

c1 = Card(Suit.SPADES, Rank.ACE)
c2 = Card(Suit.HEARTS, Rank.TEN)
print(f"我的牌: {c1}, 你的牌: {c2}")
print(f"我比你大吗？ {c1 > c2}")