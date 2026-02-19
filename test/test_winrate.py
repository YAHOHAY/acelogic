import httpx
import random
import time

from ace_logic.utils.logger import setup_logger

# ==========================================
# 1. 架构师级别的日志配置 (Logging Setup)
# ==========================================
# 配置日志输出格式：[时间] - [级别] - [消息]

logger = setup_logger(__name__)
# ==========================================
# 2. 数据准备区
# ==========================================
suits = ['s', 'h', 'd', 'c']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
full_deck = [r + s for r in ranks for s in suits]

dirty_names = [
    "  JohnDoe  ", "alice_smith", "BOB ", "", "  ", "unknown",
    "ProPlayer99", "   jack", "QUEEN  "
]


def generate_random_payload():
    """随机生成合法的德州扑克请求参数"""
    deck = full_deck.copy()
    random.shuffle(deck)
    hole_cards = [deck.pop(), deck.pop()]
    stage = random.choices([0, 3, 4, 5], weights=[50, 30, 10, 10])[0]
    community_cards = [deck.pop() for _ in range(stage)]

    return {
        "hole_cards": hole_cards,
        "community_cards": community_cards,
        "opponent_count": random.randint(1, 6),
        "user_name": random.choice(dirty_names)
    }

def test_generate_random_payload():
    API_URL = "http://127.0.0.1:8000/win_rate"
    TOTAL_REQUESTS = 1000

    # 替换 print 为 logger.info
    logger.info(f"🚀 开始向 AceLogic 引擎注入 {TOTAL_REQUESTS} 条模拟对局数据...")
    start_time = time.time()
    success_count = 0

    with httpx.Client() as client:
        for i in range(TOTAL_REQUESTS):
            payload = generate_random_payload()
            try:
                response = client.post(API_URL, json=payload, timeout=10.0)
                if response.status_code == 200:
                    success_count += 1
                else:
                    # 如果接口返回 400 或 500，使用 warning 级别记录
                    logger.warning(f"请求失败，状态码: {response.status_code}, 报文: {response.text}")
            except Exception as e:
                # 如果出现网络断开等严重异常，使用 error 级别记录
                logger.error(f"网络请求异常: {e}")

            # 进度播报
            if (i + 1) % 50 == 0:
                logger.info(f"⏳ 已处理 {i + 1} / {TOTAL_REQUESTS} 条...")

    elapsed = time.time() - start_time
    logger.info(f"✅ 注入完成！耗时 {elapsed:.2f} 秒。成功生成 {success_count} 条数据。")
