from collections import Counter
from itertools import combinations

from ace_logic.core.card import Card, Rank
from ace_logic.core.exceptions import InvalidHandSizeError
from ace_logic.utils.logger import setup_logger

logger = setup_logger(__name__)


STRAIGHT_MASKS = [
    0x1F00, # 10-J-Q-K-A (1111100000000) - 大顺子 (Broadway)
    0x0F80, # 9-10-J-Q-K  (0111110000000)
    0x07C0, # 8-9-10-J-Q  (0011111000000)
    0x03E0, # 7-8-9-10-J  (0001111100000)
    0x01F0, # 6-7-8-9-10  (0000111110000)
    0x00F8, # 5-6-7-8-9   (0000011111000)
    0x007C, # 4-5-6-7-8   (0000001111100)
    0x003E, # 3-4-5-6-7   (0000000111110)
    0x001F, # 2-3-4-5-6   (0000000011111)
    0x100F  # A-2-3-4-5   (1000000001111) - 小顺子 (Wheel, A在这里当1用)
]
class HandEvaluator:
    @staticmethod
    def is_flush(cards: list[Card]) -> bool:
        return (cards[0].value & cards[1].value & cards[2].value & cards[3].value & cards[4].value & 0xF000) != 0
    @staticmethod
    def _is_straight(cards: list[Card]) -> bool:

        hand_mask = (cards[0].value | cards[1].value | cards[2].value |
                     cards[3].value | cards[4].value) & 0x1FFF
        return hand_mask in STRAIGHT_MASKS  # 这是一个包含 10 个整数的预设集合





    @staticmethod
    def evaluate(cards: list[Card]) -> tuple:
        #FIx start
        if isinstance(cards, tuple):
            cards = list(cards)
        #Fix end

        if len(cards) != 5 :
            logger.error(f"Evaluation failed: Expected 5 cards, got {len(cards)}")
            raise InvalidHandSizeError("Exactly 5 cards are required for evaluation.")
        cards.sort(reverse=True)
        ranks = [c.rank for c in cards]
        suits = [c.suit for c in cards]
        rank_counts = Counter(ranks)
        sorted_counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        counts_only = [item[1] for item in sorted_counts]
        ranked_values = [item[0] for item in sorted_counts]
        # 3. Check for Flush and Straight (检查同花和顺子)
        is_flush = len(set(suits)) == 1
        is_straight = HandEvaluator._is_straight(ranks)
        # 4. Pattern Matching and Scoring (模式匹配与打分)
        # Rank Scores: Straight Flush=8, Four of a Kind=7, Full House=6 ... High Card=0
        if is_flush and is_straight:
            # Check for Royal Flush (14 is ACE, 10 is TEN)
            score = 9 if ranks[0] == Rank.ACE and ranks[-1] == Rank.TEN else 8
            return (score, ranks)

        if counts_only == [4, 1]: return (7, ranked_values)  # Four of a Kind (四条)
        if counts_only == [3, 2]: return (6, ranked_values)  # Full House (葫芦)
        if is_flush: return (5, ranks)  # Flush (同花)
        if is_straight: return (4, ranks)  # Straight (顺子)
        if counts_only == [3, 1, 1]: return (3, ranked_values)  # Three of a Kind (三条)
        if counts_only == [2, 2, 1]: return (2, ranked_values)  # Two Pair (两对)
        if counts_only == [2, 1, 1, 1]: return (1, ranked_values)  # One Pair (对子)

        return (0, ranks)  # High Card (高牌)
    @staticmethod
    def get_best_hand(seven_cards : list[Card]):
        """
                Texas Hold'em '7-choose-5' logic.
                (德州扑克 7 选 5 核心逻辑)
                """
        # combinations(seven_cards, 5) generates all 21 possible combinations
        all_combinations = combinations(seven_cards, 5)

        # Maximize based on the score tuple returned by evaluate()
        # (基于 evaluate 返回的元组找出最大值)
        best_hand = max(all_combinations, key=HandEvaluator.evaluate)
        return best_hand, HandEvaluator.evaluate(best_hand)
    @staticmethod
    def evaluate_to_str(num : int) -> str:
        return [
        "High Card", "Pair", "Two Pair", "Three of a Kind",
        "Straight", "Flush", "Full House", "Four of a Kind",
        "Straight Flush", "Royal Flush"
    ][num]






