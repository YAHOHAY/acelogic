from fastapi import FastAPI, Query
from ace_logic.core.deck import Deck
from ace_logic.utils.evaluator import HandEvaluator
from ace_logic.core.exceptions import AceLogicError
from ace_logic.utils.logger import setup_logger

# 初始化 Logger，名字叫 ace_logic.api
logger = setup_logger("ace_logic.api")

app = FastAPI(title="AceLogic Poker API", description="专业德州扑克逻辑后端")


@app.get("/")
def read_root():
    return {"message": "Welcome to AceLogic Poker API", "status": "online"}


@app.get("/deal")
def deal_cards(count: int = Query(5, gt=0, le=52)):
    """
    发牌接口：可以通过 ?count=5 来指定张数
    """
    try:
        deck = Deck()
        deck.shuffle()
        cards = deck.deal(count)

        logger.info(f"API Deal: Successfully dealt {count} cards via Web.")
        return {
            "success": True,
            "cards": [str(c) for c in cards],
            "remaining": len(deck._cards)
        }
    except AceLogicError as e:
        logger.error(f"API Error: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/evaluate_best")
def evaluate_best():
    """
    模拟一局 7 选 5 的最佳牌型判定
    """
    deck = Deck()
    deck.shuffle()

    # 模拟公共牌和底牌
    seven_cards = deck.deal(7)
    best_hand, score = HandEvaluator.get_best_hand(seven_cards)

    return {
        "all_cards": [str(c) for c in seven_cards],
        "best_hand": [str(c) for c in best_hand],
        "hand_type_score": score[0],
        "rank_details": score[1]
    }