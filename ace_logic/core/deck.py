import random
from typing import List

from ace_logic.core.card import Card, Suit, Rank


class Deck:
    """牌堆类：管理 52 张扑克牌"""

    def __init__(self):
        # 核心亮点：使用列表推导式一行生成 52 张牌，优雅且高效
        self._cards: List[Card] = [Card(suit, rank) for suit in Suit for rank in Rank]

    def shuffle(self) -> None:
        """洗牌：直接利用 Python 标准库的强大功能"""
        random.shuffle(self._cards)

    def deal(self, num: int) -> List[Card]:
        """
        发牌：从牌堆顶部弹出指定数量的牌
        :param num: 发牌数量
        :return: 弹出的 Card 对象列表
        """
        if num > len(self._cards):
            # 这里的异常处理体现了后端开发的防御性编程思维
            raise ValueError(f"牌堆剩余牌量不足！剩余: {len(self._cards)}, 请求: {num}")

        dealt_cards = [self._cards.pop() for _ in range(num)]
        return dealt_cards

    def __len__(self) -> int:
        """魔术方法：允许直接调用 len(deck_instance) 获取剩余牌数"""
        return len(self._cards)

    def __repr__(self) -> str:
        return f"Deck(remaining={len(self._cards)})"