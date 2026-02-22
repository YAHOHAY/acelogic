import time

from ace_logic.core.deck import Deck
from ace_logic.utils.evaluator import HandEvaluator
from ace_logic.utils.ratecalculate import WinRateCalculator
from langgraph.graph_demo import app
HandEvaluator.load_lookup_table()
class AceLogicGame:
    def __init__(self, players_info: dict, ai_app, initial_stack: int = 1000):
        self.ai_app = ai_app
        self.deck = Deck()
        self.calculator = WinRateCalculator(iterations=5000)

        # 初始化玩家名单
        self.players = list(players_info.keys())

        # 🌟 构建全局共享状态 (State)
        self.state = {
            "pot": 0,
            "community_cards": [],  # 注意：存的是 Card 对象的字符串表达，方便 AI 阅读
            "current_max_bet": 0,
            "action_history": ["--- 新的一局开始了 ---"],

            "players": self.players,
            "current_player_idx": 0,
            "player_positions": {"Alice": "SB", "Bob": "BB", "Charlie": "BTN"},  # 简写位置
            "player_stacks": {p: initial_stack for p in self.players},
            "player_status": {p: "active" for p in self.players},
            "player_current_bets": {p: 0 for p in self.players},
            "player_acted": {p: False for p in self.players},

            "hole_cards": {p: [] for p in self.players},
            "win_rates": {p: 0.0 for p in self.players},
            "personas": players_info
        }

        # 后端私有变量（不直接喂给 AI 的原始 Card 对象）
        self._private_hole_cards = {p: [] for p in self.players}
        self._private_community_cards = []

    def run_full_hand(self):
        print("\n" + "🃏" * 25)
        print("🚀 AceLogic 引擎点火：新牌局正式开始！")
        print("🃏" * 25)

        # 1. 翻牌前 (Pre-Flop)：发底牌
        self.deck.shuffle()
        for p in self.players:
            cards = self.deck.deal(2)
            self._private_hole_cards[p] = cards
            # 转成字符串存入 State 供 AI 阅读 (例如: ['A♠', 'K♥'])
            self.state["hole_cards"][p] = [str(c) for c in cards]

            # (这里省略了强制扣除盲注的代码，直接进入下注圈)
        self._play_street("翻牌前 (Pre-Flop)")

        # 2. 翻牌圈 (Flop)：发 3 张公共牌
        if self._can_continue_betting():
            self._deal_community_cards(3)
            self._play_street("翻牌圈 (Flop)")

        # 3. 转牌圈 (Turn)：发 1 张公共牌
        if self._can_continue_betting():
            self._deal_community_cards(1)
            self._play_street("转牌圈 (Turn)")

        # 4. 河牌圈 (River)：发 1 张公共牌
        if self._can_continue_betting():
            self._deal_community_cards(1)
            self._play_street("河牌圈 (River)")

        # 5. 结算阶段 (Showdown)
        self._showdown()

    # ================= 核心子流程 =================

    def _play_street(self, stage_name: str):
        """执行一个完整的下注圈 (Street)"""
        print(f"\n{'=' * 50}")
        print(f"🌊 进入阶段: {stage_name}")
        print(f"{'=' * 50}")

        self.state["stage"] = stage_name

        # 【清盘】：每一条街开始前，重置大家本轮的表态和下注额
        self.state["current_max_bet"] = 0
        self.state["current_player_idx"] = 0
        for p in self.players:
            self.state["player_acted"][p] = False
            self.state["player_current_bets"][p] = 0

        # 每次发完新牌，重算胜率！(调用你硬核的 C 级别蒙特卡洛算法)
        self._update_win_rates()

        # 🚀 将控制权正式移交 LangGraph AI 状态机！
        print(f"[后端] 正在唤醒 AI 代理网络进行 {stage_name} 博弈...")
        self.state = self.ai_app.invoke(self.state)
        time.sleep(1)  # 稍微停顿，让输出更有节奏感

    def _deal_community_cards(self, count: int):
        """后端荷官发公共牌"""
        new_cards = self.deck.deal(count)
        self._private_community_cards.extend(new_cards)
        # 更新给 AI 看的字符串列表
        self.state["community_cards"] = [str(c) for c in self._private_community_cards]
        print(f"\n[荷官] 发出 {count} 张公共牌: {[str(c) for c in new_cards]}")

    def _update_win_rates(self):
        """调用你手搓的 WinRateCalculator"""
        print("[后台算力] 正在进行蒙特卡洛胜率模拟...")
        active_count = sum(1 for status in self.state["player_status"].values() if status in ["active", "all_in"])

        if active_count <= 1:
            return  # 只有 1 个人了，不用算了

        for p in self.players:
            if self.state["player_status"][p] in ["active", "all_in"]:
                my_cards = self._private_hole_cards[p]
                comm_cards = self._private_community_cards
                # 调用你的硬核算法
                equity = self.calculator.calculate(my_cards, comm_cards, opponent_count=active_count - 1)
                self.state["win_rates"][p] = round(equity, 4)

    def _can_continue_betting(self) -> bool:
        """检查是否还有至少 2 个能自由活动的玩家"""
        active_count = sum(1 for status in self.state["player_status"].values() if status == "active")
        return active_count >= 2

    def _showdown(self):
        """核心步骤 5：最终摊牌与比大小结算"""
        print("\n" + "💰" * 25)
        print("🏆 牌局结束，进入最终摊牌结算 (Showdown)！")

        # 1. 补齐 5 张公共牌 (防范由于 All-in 导致的提早结束)
        missing_cards = 5 - len(self._private_community_cards)
        if missing_cards > 0:
            print(f"[荷官] 发完剩余的 {missing_cards} 张公共牌...")
            self._deal_community_cards(missing_cards)

        print(f"\n[最终公共牌]：{self.state['community_cards']}")
        print(f"[最终总底池]：{self.state['pot']}\n")

        # 2. 筛选出有资格参与结算的玩家 (弃牌的没资格)
        showdown_players = [p for p in self.players if self.state["player_status"][p] in ["active", "all_in"]]

        # 极端情况：如果只有 1 个人存活（其他人都 Fold 了），他直接赢走底池
        if len(showdown_players) == 1:
            winner = showdown_players[0]
            print(f"🎉 所有对手已弃牌！[{winner}] 不战而胜，赢走底池 {self.state['pot']}！")
            self.state["player_stacks"][winner] += self.state["pot"]
            return

        # 3. 核心大戏：调用你的硬核 Evaluator 进行牌力比对！
        print("--- ⚔️ 亮牌比大小 ---")
        player_results = {}
        for p in showdown_players:
            # 拼凑 7 张牌：2张底牌 + 5张公共牌
            seven_cards = self._private_hole_cards[p] + self._private_community_cards

            # 👉 呼叫你的极速算法！
            best_5_cards, (score, mask) = HandEvaluator.get_best_hand(seven_cards)

            # 翻译成人类能看懂的牌型名称 (假设你有这个方法)
            hand_name = HandEvaluator.evaluate_to_str(score)

            player_results[p] = {
                "score": score,
                "best_5": best_5_cards,
                "hand_name": hand_name
            }

            print(
                f"[{p}] 底牌 {self.state['hole_cards'][p]}  ==>  最佳5张: {[str(c) for c in best_5_cards]} ({hand_name})")

        # 4. 决出胜负，分发奖金 (处理平局 Split Pot)
        # 找出最高分
        max_score = max(data["score"] for data in player_results.values())

        # 找出所有拥有最高分的玩家 (可能有多个，这就叫平局平分底池)
        winners = [p for p, data in player_results.items() if data["score"] == max_score]

        print("\n" + "🌟" * 25)
        if len(winners) == 1:
            winner = winners[0]
            print(f"🎉 恭喜赢家：[{winner}] 凭借 【{player_results[winner]['hand_name']}】 独吞底池 {self.state['pot']}！")
            self.state["player_stacks"][winner] += self.state["pot"]
        else:
            # 平局情况
            print(f"🤝 惊天平局！赢家是：{winners}，共同凭借 【{player_results[winners[0]]['hand_name']}】 平分底池！")
            split_amount = self.state["pot"] // len(winners)  # 整除防小数
            for w in winners:
                self.state["player_stacks"][w] += split_amount
                print(f"   -> [{w}] 分得筹码: {split_amount}")

        print("💰" * 25 + "\n")


# ==========================================
# 🚀 启动入口
# ==========================================
if __name__ == "__main__":
    # 你的 AI 性格设定字典
    players_info = {
        "Alice": "极其紧凶（TAG）的职业老手。没有好牌绝不入池，有好牌必重拳出击。",
        "Bob": "松弱（Calling Station）的娱乐玩家。一点点牌就不想走，喜欢一直跟注。",
        "Charlie": "极其激进的疯子（Maniac）。喜欢用超大下注诈唬别人。"
    }

    # 实例化游戏引擎，注入你的 ai_app (LangGraph 编译后的应用)
    # 注意：这里假设你之前的 app = workflow.compile() 已经写好了
    game = AceLogicGame(players_info=players_info, ai_app=app, initial_stack=1000)

    # 执行完整的一局！
    game.run_full_hand()