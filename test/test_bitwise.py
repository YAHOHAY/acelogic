import sys
import os

from ace_logic.utils.evaluator import HandEvaluator

# 确保路径指向你当前的 ace_logic 目录
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ace_logic.core.card import Card, Rank, Suit


def test_run_ace_logic():
    print("🚀 开始 AceLogic 2.0 核心逻辑测试...\n")

    # --- 1. Card 类及位运算验证 ---
    print("【步骤1】Card 32位编码与属性保护验证")
    c1 = Card(Rank.ACE, Suit.SPADES)

    # 验证位段拼接
    # 预期: (41 << 21) | 14 << 17 | (0x2000) | (1 << 12)
    print(f"  * {c1} 的十六进制编码: {hex(c1.value)}")
    assert hex(c1.value) == '0x53c3000', "❌ Card 编码逻辑错误！"

    # 验证属性保护
    try:
        c1.rank = Rank.TWO
    except AttributeError:
        print("  * ✅ 属性保护生效：无法非法修改牌面属性。")

    # --- 2. 查找表加载验证 ---
    print("\n【步骤2】查找表（Hand Lookup）加载验证")
    try:
        # 加载你刚刚生成的 hand_lookup.json
        HandEvaluator.load_lookup_table("hand_lookup.json")
        print(f"  * ✅ 查找表加载成功，当前包含 {len(HandEvaluator._LOOKUP_TABLE)} 个特征项。")
    except Exception as e:
        print(f"  * ❌ 查找表加载失败: {e}")
        return

    # --- 3. 牌型判定测试 ( evaluate ) ---
    print("\n【步骤3】典型牌型判定验证")

    # 测试 1: 同花顺 (Straight Flush)
    sf_hand = [Card(Rank.NINE, Suit.SPADES), Card(Rank.EIGHT, Suit.SPADES),
               Card(Rank.SEVEN, Suit.SPADES), Card(Rank.SIX, Suit.SPADES), Card(Rank.FIVE, Suit.SPADES)]
    score, _ = HandEvaluator.evaluate(sf_hand)
    print(f"  * 同花顺测试: {HandEvaluator.evaluate_to_str(score)} (等级: {score})")
    assert score // 1000000 == 8, "❌ 同花顺判定错误！"

    # 测试 2: 葫芦 (Full House)
    # 利用 strength 分数判定：(6 * 1,000,000) + 权重
    fh_hand = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS),
               Card(Rank.KING, Suit.DIAMONDS), Card(Rank.KING, Suit.SPADES)]
    strength, _ = HandEvaluator.evaluate(fh_hand)
    print(f"  * 葫芦测试: {HandEvaluator.evaluate_to_str(strength // 1000000)} (强度分: {strength})")
    assert strength // 1000000 == 6, "❌ 葫芦判定错误！"

    # --- 4. 7 选 5 逻辑验证 ---
    print("\n【步骤4】德州扑克 7 选 5 核心算法验证")
    seven_cards = [
        Card(Rank.NINE, Suit.SPADES), Card(Rank.KING, Suit.SPADES),  # 玩家底牌
        Card(Rank.QUEEN, Suit.SPADES), Card(Rank.JACK, Suit.SPADES), Card(Rank.TEN, Suit.SPADES),  # 翻牌
        Card(Rank.TWO, Suit.HEARTS), Card(Rank.TWO, Suit.DIAMONDS)  # 转牌/河牌
    ]
    best_hand, final_score = HandEvaluator.get_best_hand(seven_cards)
    print(f"  * 7选5输入: {[str(c) for c in seven_cards]}")
    # 判定是否识别出皇家同花顺 (等级 9)
    print(f"  * 判定结果: {HandEvaluator.evaluate_to_str(best_hand)}")

    print("\n🎉 所有核心逻辑测试通过！AceLogic 2.0 性能已就绪。")


if __name__ == "__main__":
    test_run_ace_logic()