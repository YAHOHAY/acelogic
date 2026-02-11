import json
import os
from collections import Counter
from itertools import combinations

from ace_logic.core.card import Card, Rank
from ace_logic.core.exceptions import InvalidHandSizeError
from ace_logic.utils.logger import setup_logger

logger = setup_logger(__name__)
ONEMILLION= 1000000


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
    _LOOKUP_TABLE = None



    @classmethod
    def load_lookup_table(cls, filename: str = "hand_lookup.json"):
        """加载生成的质数查找表 (智能路径版)"""
        if cls._LOOKUP_TABLE is None:
            # 1. 获取 evaluator.py 这个文件所在的绝对路径
            # 例如: C:\Users\preju\...\AceLogic\ace_logic\utils
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # 2. 往上回溯两层，找到项目根目录 (AceLogic/)
            # utils -> ace_logic -> AceLogic (Root)
            project_root = os.path.dirname(os.path.dirname(current_dir))

            # 3. 拼接出 json 文件的绝对路径
            json_path = os.path.join(project_root, filename)

            # 4. 双重保险：如果根目录找不到，试试当前目录（防止文件被移动）
            if not os.path.exists(json_path):
                # 备选方案：就在当前脚本运行目录下找
                json_path = filename

            try:
                with open(json_path, "r") as f:
                    # JSON 的 key 是字符串，需要转回 int 方便 $O(1)$ 查询
                    cls._LOOKUP_TABLE = {int(k): v for k, v in json.load(f).items()}
                print(f"✅ 成功加载查找表: {json_path}")
            except FileNotFoundError:
                # 抛出更友好的错误信息，告诉我们它到底去哪找了
                raise FileNotFoundError(f"❌ 找不到查找表! 尝试路径: {json_path}")

        return cls._LOOKUP_TABLE

    @staticmethod
    def evaluate_fast(card_values: tuple) -> int:
        """
        ⚡️ 极速内核：只接收整数元组，不处理 Card 对象。
        去掉所有对象访问，只做位运算。
        """
        hand_mask = 0
        suit_check = 0x1E000
        prime_prod = 1

        # 在 C 语言层面的迭代速度：tuple > list
        for val in card_values:
            hand_mask |= (val & 0x1FFF)
            suit_check &= (val & 0x1E000)
            prime_prod *= (val >> 21)

        # 逻辑与之前一致，但全是局部变量和整数
        if suit_check:  # 非0即为True，比 != 0 微快
            if hand_mask in STRAIGHT_MASKS:
                return 9000000 + hand_mask if hand_mask == 0x1F00 else 8000000 + hand_mask
            return 5000000 + hand_mask

        if hand_mask in STRAIGHT_MASKS:
            return 4000000 + hand_mask

        return HandEvaluator._LOOKUP_TABLE.get(prime_prod, 0)





    @staticmethod
    def evaluate(cards: list[Card]) -> tuple[int, int]:
        """兼容旧接口的慢速版 (用于单次调用或展示)"""
        # 即使是旧接口，也可以利用 fast 版加速
        values = tuple(c.value for c in cards)
        score = HandEvaluator.evaluate_fast(values)
        # 重新计算 mask 用于返回
        mask = 0
        for v in values: mask |= (v & 0x1FFF)
        return (score, mask)

    @staticmethod
    def get_best_hand(seven_cards: list[Card]):
        """
        🚀 优化后的 7 选 5：
        1. 对象 -> 整数 (只做 1 次)
        2. 整数排列组合 (C 语言级循环)
        3. 整数评估
        4. 整数 -> 对象还原 (只做 1 次)
        """
        # 1. 预处理：建立 整数->对象 的映射，同时提取 value
        # 这里用 list 而不是 dict.values() 是为了保证顺序，方便还原
        card_map = {c.value: c for c in seven_cards}
        raw_values = list(card_map.keys())

        # 2. 核心加速：itertools 处理 int 比处理 Card 对象快得多
        # 生成的是 (int, int, int, int, int) 的元组流
        all_combinations_vals = combinations(raw_values, 5)

        best_score = -1
        best_vals = None

        # 3. 极速循环 (Hot Path)
        # 这里没有任何 .value 访问，没有对象创建，只有纯粹的数字计算
        for combo_vals in all_combinations_vals:
            score = HandEvaluator.evaluate_fast(combo_vals)
            if score > best_score:
                best_score = score
                best_vals = combo_vals

        # 4. 还原结果：从最好的 5 个 int 找回 5 个 Card 对象
        best_hand_cards = [card_map[v] for v in best_vals]

        # 计算辅助掩码 (低频操作，不影响大局)
        final_mask = 0
        for v in best_vals: final_mask |= (v & 0x1FFF)

        return best_hand_cards, (best_score, final_mask)

    @staticmethod
    def evaluate_to_str(strength: int) -> str:
        rank_level = strength // 1000000
        if rank_level > 9: rank_level = 0

        names = [
            "High Card", "Pair", "Two Pair", "Three of a Kind",
            "Straight", "Flush", "Full House", "Four of a Kind",
            "Straight Flush", "Royal Flush"
        ]
        return names[rank_level]





