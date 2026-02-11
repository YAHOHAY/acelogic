import random
from typing import List
from ace_logic.core.card import Card, Rank, Suit
from ace_logic.utils.evaluator import HandEvaluator


class WinRateCalculator:
    def __init__(self, iterations: int = 10000):
        self.iterations = iterations
        self.full_deck = [Card(r, s) for r in Rank for s in Suit]

    def calculate(self, my_hole_cards: List[Card], community_cards: List[Card], opponent_count: int = 1) -> float:
        wins = 0
        ties = 0

        known_cards = my_hole_cards + community_cards
        remaining_deck = [c for c in self.full_deck if c not in known_cards]

        # 计算每次模拟总共需要抽取的牌数：补齐公共牌 + 对手底牌
        needed_community_count = 5 - len(community_cards)
        total_needed = needed_community_count + (opponent_count * 2)

        for _ in range(self.iterations):
            # --- 核心优化：按需抽样 ---
            # 这一步直接完成了“洗牌”并“发出”了所有模拟需要的牌
            sim_cards = random.sample(remaining_deck, k=total_needed)

            # 分配模拟的公共牌
            sim_community = community_cards + sim_cards[:needed_community_count]

            # 分配对手底牌并评估
            opponents_best_scores = []
            for i in range(opponent_count):
                # 按照偏移量精准切片
                start = needed_community_count + (i * 2)
                opp_hole = sim_cards[start: start + 2]
                _, (opp_score, _) = HandEvaluator.get_best_hand(opp_hole + sim_community)
                opponents_best_scores.append(opp_score)

            # 评估自己的牌力
            _, (my_score, _) = HandEvaluator.get_best_hand(my_hole_cards + sim_community)

            # 胜负判定逻辑
            max_opp_score = max(opponents_best_scores)
            if my_score > max_opp_score:
                wins += 1
            elif my_score == max_opp_score:
                ties += 1

        # 胜率公式：$WinRate = \frac{Wins + \frac{Ties}{2}}{TotalSimulations}$
        return (wins + (ties / 2)) / self.iterations