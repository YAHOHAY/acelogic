from collections import Counter
from ace_logic.core.card import Card, Rank


class OldHandEvaluator:
    @staticmethod
    def _is_straight(ranks):
        # 兼容 IntEnum 的数值比较
        rank_values = [r.value for r in ranks]
        low_straight = [14, 5, 4, 3, 2]  # A-2-3-4-5 的数值
        if sorted(rank_values, reverse=True) == low_straight:
            return True
        return (max(rank_values) - min(rank_values)) == 4 and len(set(rank_values)) == 5

    @staticmethod
    def evaluate(cards):
        # 适配：手动按照 rank 的数值进行排序，不依赖 Card 对象的比较
        sorted_cards = sorted(cards, key=lambda x: x.rank.value, reverse=True)

        ranks = [c.rank for c in sorted_cards]
        suits = [c.suit for c in sorted_cards]

        rank_counts = Counter(ranks)
        # 根据频率和点数排序
        sorted_counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0].value), reverse=True)

        counts_only = [item[1] for item in sorted_counts]
        ranked_values = [item[0] for item in sorted_counts]

        is_flush = len(set(suits)) == 1
        is_straight = OldHandEvaluator._is_straight(ranks)

        if is_flush and is_straight:
            score = 9 if ranks[0] == Rank.ACE and ranks[-1] == Rank.TEN else 8
            return (score, ranks)

        if counts_only == [4, 1]: return (7, ranked_values)
        if counts_only == [3, 2]: return (6, ranked_values)
        if is_flush: return (5, ranks)
        if is_straight: return (4, ranks)
        if counts_only == [3, 1, 1]: return (3, ranked_values)
        if counts_only == [2, 2, 1]: return (2, ranked_values)
        if counts_only == [2, 1, 1, 1]: return (1, ranked_values)

        return (0, ranks)