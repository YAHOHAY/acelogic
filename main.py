from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import time
from contextlib import asynccontextmanager # 引入这个用于生命周期管理

from ace_logic.core.card import Card, Rank, Suit
from ace_logic.utils.evaluator import HandEvaluator
from ace_logic.utils.ratecalculate import WinRateCalculator


# --- 1. 定义生命周期管理器 (Lifespan) ---
# 这是 FastAPI 推荐的“预热”方式：在服务启动前把重型资源加载好
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 System Startup: Loading Lookup Table...")
    HandEvaluator.load_lookup_table() # <--- 关键！显式加载表
    print(f"✅ Lookup Table Loaded. Engine is ready.")
    yield
    print("🛑 System Shutdown.")

# --- 2. 注入生命周期 ---
app = FastAPI(title="AceLogic API", version="2.0", lifespan=lifespan)

# 3. 初始化计算器 (保持不变)

calculator = WinRateCalculator(iterations=10000)

# --- 定义请求/响应模型 ---
class WinRateRequest(BaseModel):
    hole_cards: List[str]  # 例如 ["Ah", "Kd"]
    community_cards: List[str] = []  # 例如 ["Qs", "Js", "Ts"]
    opponent_count: int = 1


class WinRateResponse(BaseModel):
    win_rate: float
    elapsed_time: float
    hands_per_second: float


# --- 辅助工具：字符串 -> Card 对象 ---
# 需要把 "Ah" 解析成 Card(Rank.ACE, Suit.HEARTS)
def parse_card(card_str: str) -> Card:
    if len(card_str) != 2:
        raise ValueError(f"Invalid card format: {card_str}")

    rank_char = card_str[0].upper()
    suit_char = card_str[1].lower()

    # 映射表
    rank_map = {
        '2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, '5': Rank.FIVE,
        '6': Rank.SIX, '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
        'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN, 'K': Rank.KING, 'A': Rank.ACE
    }
    # 注意：你的 Suit 定义值是位掩码，这里只做映射
    suit_map = {
        's': Suit.SPADES, 'h': Suit.HEARTS,
        'd': Suit.DIAMONDS, 'c': Suit.CLUBS
    }

    if rank_char not in rank_map or suit_char not in suit_map:
        raise ValueError(f"Unknown card: {card_str}")

    return Card(rank_map[rank_char], suit_map[suit_char])


@app.post("/win_rate", response_model=WinRateResponse)
async def calculate_win_rate(request: WinRateRequest):
    """
    计算胜率的核心接口
    """
    try:
        # 1. 解析卡牌字符串
        my_hole = [parse_card(c) for c in request.hole_cards]
        community = [parse_card(c) for c in request.community_cards]

        # 2. 计时开始
        start_time = time.perf_counter()

        # 3. 调用蒙特卡洛引擎
        rate = calculator.calculate(my_hole, community, request.opponent_count)

        # 4. 计时结束
        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # 计算吞吐量 (每次模拟涉及 opponent_count + 1 个玩家)
        # 这里的 throughput 估算比较粗略，主要看 elapsed

        return WinRateResponse(
            win_rate=rate,
            elapsed_time=elapsed,
            hands_per_second=calculator.iterations / elapsed
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def health_check():
    return {"status": "AceLogic 2.0 is running", "engine": "Integer Stream Optimized"}