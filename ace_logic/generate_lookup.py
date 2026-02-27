
import json
import itertools
from ace_logic.core.card import Card, Rank, Suit
from old_logic import OldHandEvaluator  # 使用你之前的旧逻辑作为判定基准


def generate_minimal_lookup():
    deck = [Card(r, s) for r in Rank for s in Suit]
    lookup_table = {}

    print("正在为 Acelogic 2.0 生成最小化查找表...")

    # 遍历 52 选 5
    for combo in itertools.combinations(deck, 5):
        # 1. 提取位特征
        hand_mask = 0
        suit_check = 0xF000
        prime_prod = 1
        for c in combo:
            val = c.value
            hand_mask |= (val & 0x1FFF)
            suit_check &= (val & 0x1E000)
            prime_prod *= (val >> 21)

        # 2. 模拟你的 evaluate 漏斗逻辑
        is_flush = (suit_check != 0)
        # 顺子判定：注意包含 A-2-3-4-5 (0x100F)
        STRAIGHT_MASKS = [0x1F00, 0x0F80, 0x07C0, 0x03E0, 0x01F0, 0x00F8, 0x007C, 0x003E, 0x001F, 0x100F]
        is_straight = hand_mask in STRAIGHT_MASKS

        # 3. 只有“漏”下来的才进表
        if not is_flush and not is_straight:
            if prime_prod not in lookup_table:
                # 使用旧逻辑获取牌型等级和点数顺序
                score, kickers = OldHandEvaluator.evaluate(list(combo))

                # 计算唯一强度分：score 是百万位，后面补齐点数权重（用于同级比较）
                # 例如：三条 8 (score=3)，权重 = 3,080,000 + 剩余杂牌贡献
                # 简单处理：将排序后的点数转为 15 进制权重
                strength = score * 1000000
                for i, r in enumerate(kickers):
                    strength += r.value * (15 ** (4 - i))

                lookup_table[prime_prod] = strength

    with open("../hand_lookup.json", "w") as f:
        json.dump(lookup_table, f)

    print(f"成功！生成了 {len(lookup_table)} 个唯一质数条目。")


if __name__ == "__main__":
    generate_minimal_lookup()
