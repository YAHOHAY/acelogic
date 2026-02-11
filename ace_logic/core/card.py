from enum import IntEnum


class Suit(IntEnum):
            """花色位掩码：分别占据二进制的第12, 13, 14, 15位"""
            SPADES = 0x2000  # 1 << 13
            HEARTS = 0x4000  # 1 << 14
            DIAMONDS = 0x8000  # 1 << 15
            CLUBS = 0x10000  # 1 << 16

class Rank(IntEnum):
    """点数：2-14，直接对应数值"""
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
    # 13个点数对应的质数（2-A）
    PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]

    # 方便人类阅读的映射
    RANK_MAP = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
                10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
    SUIT_MAP = {0x2000: '♠', 0x4000: '♥', 0x8000: '♦', 0x10000: '♣'}

    def __init__(self, rank: Rank, suit: Suit):
        self._rank = rank
        self._suit = suit
        # 0-12位: 点数掩码
        bitmask = 1 << (rank.value - 2)

        # 13-16位: 花色掩码
        suit_mask = suit.value

        # 17-20位: 点数数值
        rank_val = rank.value << 17

        # 21-26位: 质数 (最大的质数41只需要6位)
        prime = self.PRIMES[rank.value - 2]
        prime_val = prime << 21

        # 组装核心编码
        self._value = prime_val | rank_val | suit_mask | bitmask

    @property
    def rank(self):
        """只读属性：外部只能 card.rank，不能 card.rank = NewRank"""
        return self._rank

    @property
    def suit(self):
        """只读属性"""
        return self._suit

    @property
    def value(self):
        """只读的核心编码：这就是 Acelogic 的真理"""
        return self._value

    def __repr__(self):
        """控制台展示：例如 'A♠'"""
        return f"{self.RANK_MAP[self.rank.value]}{self.SUIT_MAP[self.suit.value]}"

    def display_binary(self):
        """调试用：查看这张牌的二进制全貌"""
        return f"{self.value:032b}"