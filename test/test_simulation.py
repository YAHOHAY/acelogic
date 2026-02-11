import unittest
from ace_logic.core.card import Card, Rank, Suit
from ace_logic.utils.ratecalculate import WinRateCalculator


#from ace_logic.calculator.win_rate import WinRateCalculator



class TestWinRateSimulation(unittest.TestCase):

    def test_aa_vs_random(self):
        """测试: 手持 AA 对抗 1 个随机对手的胜率 (Pre-flop)"""
        # 你的底牌: A♠ A♥
        my_hole = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
        community = []  # 翻牌前

        # 运行模拟 (降低次数以加快测试速度)
        sim = WinRateCalculator(iterations=10000)
        win_rate = sim.calculate(my_hole, community, opponent_count=1)

        print(f"\n🧪 Simulation Result (AA vs Random): {win_rate:.2%}")

        # AA 对随机牌的胜率通常在 85% 左右
        self.assertTrue(0.80 <= win_rate <= 0.90, f"AA win rate {win_rate} seems off (expected ~85%)")

    def test_flop_simulation(self):
        """测试: 翻牌圈已中四条的必胜局"""
        # 你的底牌: 8♠ 8♥
        # 翻牌: 8♦ 8♣ A♠
        # 你已经四条了，这局几乎必胜 (除非对手有 AA 且转河发 A，概率极低)
        my_hole = [Card(Rank.EIGHT, Suit.SPADES), Card(Rank.EIGHT, Suit.HEARTS)]
        community = [Card(Rank.EIGHT, Suit.DIAMONDS), Card(Rank.EIGHT, Suit.CLUBS), Card(Rank.ACE, Suit.SPADES)]

        sim = WinRateCalculator(iterations=1000)
        win_rate = sim.calculate(my_hole, community, opponent_count=1)

        print(f"🧪 Simulation Result (Flopped Quads): {win_rate:.2%}")
        self.assertGreater(win_rate, 0.99, "Flopped Quads should satisfy > 99% win rate")


if __name__ == '__main__':
    unittest.main()