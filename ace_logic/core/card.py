from enum import Enum, IntEnum
from typing import Optional


class Suit(Enum):
    """花色枚举：使用 Unicode 字符增强控制台展示效果"""
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


class Rank(IntEnum):
    """点数枚举：继承 IntEnum 方便直接进行大小比较"""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Card:
    """扑克牌类：这是项目的原子级模型"""

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self) -> str:
        """
        魔术方法：定义对象在 print 或调试时的显示方式。
        脱颖而出点：不仅显示 A，还能显示 ACE 的权重。
        """
        return f"{self.suit.value}{self.rank.name.capitalize()}"

    def __eq__(self, other: object) -> bool:
        """判断两张牌是否相等"""
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __lt__(self, other: 'Card') -> bool:
        """定义小于逻辑，方便后续对整手牌进行排序"""
        return self.rank < other.rank