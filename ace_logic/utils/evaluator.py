from collections import Counter
from itertools import combinations

from ace_logic.core.card import Card, Rank


class HandEvaluator:
    @staticmethod
    def _is_straight(ranks: list[Rank]) -> bool:
        """判定是否为顺子的辅助方法"""
        # 处理德州扑克特殊顺子：A-2-3-4-5
        low_straight = [Rank.ACE, Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO]
        if ranks == low_straight:
            return True
        return (max(ranks) - min(ranks)) == 4 and len(set(ranks)) == 5
    @staticmethod
    def evaluate(cards: list[Card]) -> tuple:
        #FIx start
        if isinstance(cards, tuple):
            cards = list(cards)
        #Fix end

        if len(cards) != 5 :
            raise ValueError("Exactly 5 cards are required for evaluation.")
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





