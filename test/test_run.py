from ace_logic.core.deck import Deck

# 1. 初始化并洗牌
deck = Deck()
print(f"新牌堆初始化完成，共 {len(deck)} 张牌。")

deck.shuffle()
print("洗牌完成。")

# 2. 模拟发牌
player_hand = deck.deal(10)
print(f"发给玩家 5 张牌: {player_hand}")
print(f"牌堆目前还剩 {len(deck)} 张。")

# 3. 排序展示（得益于你在 Card 类写的 __lt__ 方法）
player_hand.sort(reverse=True)
print(f"按点数从大到小排序: {player_hand}")