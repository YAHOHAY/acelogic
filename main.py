import sys
from ace_logic.core.deck import Deck
from ace_logic.utils.evaluator import HandEvaluator
from ace_logic.utils.logger import setup_logger
from ace_logic.core.exceptions import AceLogicError

# 1. 动态获取当前模块的 logger (动态模块名)
logger = setup_logger(__name__)


def play_one_round():
    """
    模拟一局完整的德州扑克对决逻辑
    """
    logger.info("--- Starting a professional Texas Hold'em simulation ---")

    try:
        # 初始化并洗牌
        deck = Deck()
        deck.shuffle()

        # 发牌逻辑 (底牌与公共牌)
        player_a_hole = deck.deal(2)
        player_b_hole = deck.deal(2)
        community_cards = deck.deal(5)

        logger.info(f"Community Cards: {community_cards}")
        logger.info(f"Player A: {player_a_hole} | Player B: {player_b_hole}")

        # 计算两名玩家的最佳 5 张牌组合
        # (这里利用了你写的 7-choose-5 逻辑)
        best_a, score_a = HandEvaluator.get_best_hand(player_a_hole + community_cards)
        best_b, score_b = HandEvaluator.get_best_hand(player_b_hole + community_cards)

        print("-" * 66)
        print(f"Player A's Best: {best_a} -> Rank: {score_a[0]}")
        print(f"Player B's Best: {best_b} -> Rank: {score_b[0]}")

        # 利用元组比较机制判定胜负
        if score_a > score_b:
            result_msg = "🏆 Result: Player A WINS!"
        elif score_a < score_b:
            result_msg = "🏆 Result: Player B WINS!"
        else:
            result_msg = "🤝 Result: It's a TIE (Split Pot)!"

        print(result_msg)
        logger.info(result_msg)

    except AceLogicError as e:
        # 这里展示了你自定义异常的威力：精准捕获业务错误
        logger.error(f"Game simulation aborted due to business error: {e}")
    except Exception as e:
        # 兜底捕获未知的系统错误
        logger.critical(f"Unexpected system crash: {e}", exc_info=True)


if __name__ == "__main__":
    # 允许通过命令行多次运行
    play_one_round()