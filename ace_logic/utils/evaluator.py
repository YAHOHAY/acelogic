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
    def evaluate(cards: list[Card]) -> tuple[int, int]:
        #FIx start
        if isinstance(cards, tuple):
            cards = list(cards)
        #Fix end

        if len(cards) != 5 :
            logger.error(f"Evaluation failed: Expected 5 cards, got {len(cards)}")
            raise InvalidHandSizeError("Exactly 5 cards are required for evaluation.")
        """
                核心评估算法：返回 (牌型等级, 辅助位掩码)
                等级: 0-高牌, 1-对子 ... 8-同花顺, 9-皇家同花顺
                """

        # 1. 提取基本特征
        # bitmask 用于顺子判定
        # suit_check 用于同花判定
        # prime_prod 用于查表判定重复点数
        hand_mask = 0
        suit_check = 0xF000
        prime_prod = 1

        for c in cards:
            val = c.value
            hand_mask |= (val & 0x1FFF)
            suit_check &= (val & 0x1E000)
            prime_prod *= (val >> 21)


        is_flush = (suit_check != 0)
        is_straight = hand_mask in STRAIGHT_MASKS

        # 2. 处理顺子和同花 (特殊逻辑，不完全依赖查表)
        if is_flush and is_straight:
            # 皇家同花顺判定 (10-J-Q-K-A 的掩码是 0x1F00)
            if hand_mask == 0x1F00:
                return (9*ONEMILLION + hand_mask, hand_mask)
            return (8*ONEMILLION+ hand_mask, hand_mask)

        if is_flush:
            return (5*ONEMILLION+ hand_mask, hand_mask)

        if is_straight:
            return (4*ONEMILLION+ hand_mask, hand_mask)

        # 3. 查表处理其余牌型 (四条、葫芦、三条、两对、一对、高牌)
        # 质数积是这些牌型的唯一标识
        if HandEvaluator._LOOKUP_TABLE is None:
            # 自动加载默认路径下的表
            HandEvaluator.load_lookup_table()

        score = HandEvaluator._LOOKUP_TABLE.get(prime_prod, 0)
        return (score, hand_mask)

    @staticmethod
    def get_best_hand(seven_cards: list[Card]):
        all_combinations = combinations(seven_cards, 5)

        # FIX: 保存 (牌组, 分数元组) 以便最后返回牌组
        # 使用 max 函数一次性搞定，减少 list append 开销
        # key 必须比 x[1][0] (即 evaluate 返回元组的第一个元素：强度分)

        # 临时包装一下以便 max 处理
        def get_score_bundle(combo):
            return (list(combo), HandEvaluator.evaluate(list(combo)))

        # 这里的 max 会遍历所有组合，对每个组合调用 get_score_bundle
        # 然后根据 key=lambda x: x[1][0] (即 strength) 找出最大的那个包
        best_combo, score_tuple = max(map(get_score_bundle, all_combinations), key=lambda x: x[1][0])

        return best_combo, score_tuple

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





