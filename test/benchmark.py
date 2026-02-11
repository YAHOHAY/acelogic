import time
import random
from ace_logic.core.card import Card, Rank, Suit
from ace_logic.utils.evaluator import HandEvaluator


def benchmark():
    print("🚀 Starting AceLogic 2.0 Benchmark...")

    # 1. 准备数据
    HandEvaluator.load_lookup_table()
    deck = [Card(r, s) for r in Rank for s in Suit]

    # 生成 100,000 组随机 7 张牌
    N = 100000
    random_hands = []
    print(f"Generating {N} random hands...")
    for _ in range(N):
        random_hands.append(random.sample(deck, 7))

    # 2. 开始压测
    print("🔥 Benchmarking get_best_hand (7-choose-5)...")
    start_time = time.time()

    for hand in random_hands:
        HandEvaluator.get_best_hand(hand)

    end_time = time.time()
    total_time = end_time - start_time

    # 3. 输出结果
    ops_per_sec = N / total_time
    print(f"\nResults:")
    print(f"Total Time: {total_time:.4f} seconds")
    print(f"Throughput: {ops_per_sec:,.0f} hands/second")

    if ops_per_sec > 20000:
        print("\n🏆 性能评级: 工业级 (Industrial Grade)")
    elif ops_per_sec > 5000:
        print("\n🥈 性能评级: 优秀 (Excellent)")
    else:
        print("\n🥉 性能评级: 尚可 (Acceptable)")


if __name__ == "__main__":
    benchmark()