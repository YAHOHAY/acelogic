# ace_logic/engine/game.py
import random
from typing import List

from ace_logic.utils.evaluator import HandEvaluator
from ace_logic.utils.ratecalculate import WinRateCalculator
from engine.dealer import Dealer
from engine.state import TableState
HandEvaluator.load_lookup_table()


class GameEngine:
    """德州扑克核心引擎：全局状态的唯一持有者"""

    def __init__(self, players_info: dict, ai_app=None, initial_stack: int = 9999):
        self.players = list(players_info.keys())
        self.ai_app = ai_app
        self.win_rate_calculator = WinRateCalculator(iterations=8000)

        # 1. 严格按照 TypedDict 初始化干净的全局内存
        self.state: TableState = {
            "stage": "Pre-Flop",
            "pot": 0,
            "community_cards": [],
            "current_max_bet": 0,
            "action_history": ["--- 新的一局开始了 ---"],
            "sb_amount": 10,
            "bb_amount": 20,
            "ante": 0,

            "players": self.players,
            "current_player_idx": 0,
            "player_positions": {},
            "player_stacks": {p: initial_stack for p in self.players},
            "player_status": {p: "active" for p in self.players},
            "player_current_bets": {p: 0 for p in self.players},
            "player_acted": {p: False for p in self.players},
            "player_total_invested": {p: 0 for p in self.players},

            "hole_cards": {p: [] for p in self.players},
            "win_rates": {p: 0.0 for p in self.players},
            "personas": players_info
        }

        # 2. 雇佣荷官，并把账本引用交给他
        self.dealer = Dealer(self.state)

    def _update_win_rates(self):
        """
        数据喂养桥梁：调用 WinRateCalculator，把结果写进全局账本
        """
        # 1. 找出还在桌上的玩家
        active_players = [p for p in self.players if self.state["player_status"][p] in ["active", "all_in"]]
        opponent_count = len(active_players) - 1

        # 如果只剩一个人或者没活人了，胜率直接 100% 或 0%
        if opponent_count <= 0:
            for p in self.players:
                self.state["win_rates"][p] = 1.0 if self.state["player_status"][p] != "folded" else 0.0
            return

        print("\n[引擎] 正在后台启动蒙特卡洛引擎，推演全局胜率...")

        # 2. 从荷官那里拿真实的物理牌（注意：你的计算器需要 Card 对象，而不是字符串）
        physical_community = self.dealer.get_physical_community_cards()
        physical_hole_cards = self.dealer.get_physical_hole_cards()

        # 3. 挨个计算并写入字典
        for p in self.players:
            if p in active_players:
                my_cards = physical_hole_cards[p]

                # 🚀 调用你的计算器！
                win_rate = self.win_rate_calculator.calculate(
                    my_hole_cards=my_cards,
                    community_cards=physical_community,
                    opponent_count=opponent_count
                )

                # 把算出来的浮点数写进全局字典里
                self.state["win_rates"][p] = win_rate
            else:
                self.state["win_rates"][p] = 0.0

        # 打印一下后台视角的胜率，方便你调试监控
        print(f"[上帝视角] 当前真实胜率: {self.state['win_rates']}")

    def start_game(self):
        """主循环剧本 (The Main Loop)"""
        print("\n" + "🚀" * 20)
        print("🎮 AceLogic 引擎点火！新的一局开始...")
        print("🚀" * 20)

        # 1. 赛前准备
        btn_idx = random.randint(0, len(self.players) - 1)
        self.dealer.assign_positions(btn_idx)
        self.dealer.collect_blinds_ante(self.state["sb_amount"], self.state["bb_amount"], self.state["ante"])
        self.dealer.deal_hole_cards()

        # 2. 翻牌前 (Pre-Flop) 必须进行
        self._play_street("Pre-Flop")

        # 3. 翻牌圈 (Flop) - 🌟 新增判定：有 2 个以上能掏钱的人才下注
        if self._count_action_players() >= 2:
            self.dealer.deal_community_cards(3)
            self._play_street("Flop")

        # 4. 转牌圈 (Turn)
        if self._count_action_players() >= 2:
            self.dealer.deal_community_cards(1)
            self._play_street("Turn")

        # 5. 河牌圈 (River)
        if self._count_action_players() >= 2:
            self.dealer.deal_community_cards(1)
            self._play_street("River")

        # 6. 终极结算：极速发牌 + 比大小
        self._ensure_five_community_cards()
        self._showdown()

    # ==========================================
    # 辅助方法替换 (极其关键)
    # ==========================================
    def _count_unfolded_players(self) -> int:
        """检查还有几个留在局里的（包括 All-in 的，用来判断要不要比大小）"""
        return sum(1 for status in self.state["player_status"].values() if status != "folded")

    def _count_action_players(self) -> int:
        """检查还有几个能【继续掏钱说话】的（只有 active 的）"""
        return sum(1 for status in self.state["player_status"].values() if status == "active")

    def _ensure_five_community_cards(self):
        """All-in 极速发牌：自动补齐桌面"""
        current_len = len(self.dealer.get_physical_community_cards())

        # 只要还有 2 个或以上的人没跑，牌就必须发满 5 张用来结算！
        if current_len < 5 and self._count_unfolded_players() >= 2:
            needed = 5 - current_len
            print(f"\n[后台发牌] 💥 触发 All-in 极速结算！荷官一口气发完剩余的 {needed} 张公共牌...")
            self.dealer.deal_community_cards(needed)

            # 顺手把最终牌面在日志里打出来，视觉效果拉满
            final_cards = [str(c) for c in self.dealer.get_physical_community_cards()]
            self.state["community_cards"] = final_cards
            print(f"[桌面] 最终公共牌面: {final_cards}")
    # ==========================================
    # 💰 核心财务与结算系统
    # ==========================================
    def _calculate_side_pots(self) -> List:
        s_players = [p for p in self.players if self.state["player_status"][p] in ["active", "all_in"]]
        post = []
        list1 = []
        for p in s_players:
            t = self.state["player_total_invested"][p]
            list1.append(t)
        levels = sorted(list(set(list1)))
        previous_level = 0
        tmp = self.state["player_total_invested"].copy()
        for level in levels:
            marginal_amount = level - previous_level
            current_pot_size = 0
            eligible_players = []
            for p in self.players:
                if tmp[p] - marginal_amount >= 0:
                    tmp[p] = tmp[p] - marginal_amount
                    current_pot_size += marginal_amount
                    if p in s_players:
                        eligible_players.append(p)
                else:
                    current_pot_size += tmp[p]
                    tmp[p] = 0
            post.append({"amount": current_pot_size, "eligible_players": eligible_players})
            # 切完更新水位
            previous_level = level
        return post

    def _showdown(self):
        """核心步骤 5：最终摊牌与多边池精准结算"""
        print("\n" + "💰" * 25)
        print("🏆 牌局结束，进入最终摊牌结算 (Showdown)！")

        # 1. 补齐 5 张公共牌 (防范由于 All-in 导致的提早结束)
        missing_cards = 5 - len(self.dealer._private_community_cards)
        if missing_cards > 0:
            print(f"[荷官] 发完剩余的 {missing_cards} 张公共牌...")
            self.dealer.deal_community_cards(missing_cards)

        print(f"\n[最终公共牌]：{self.state['community_cards']}")
        print(f"[最终总底池]：{self.state['pot']}\n")

        # ==========================================
        # 🌟 2. 召唤你的硬核算法，获取边池切分列表！
        # ==========================================
        pots = self._calculate_side_pots()

        # ==========================================
        # 🌟 3. 逐个池子比大小，精准发钱！
        # ==========================================
        for i, pot_info in enumerate(pots):
            pot_money = pot_info["amount"]
            eligible = pot_info["eligible_players"]
            pot_name = "主池 (Main Pot)" if i == 0 else f"边池 {i} (Side Pot {i})"

            print(f"\n--- ⚔️ 结算 {pot_name} | 金额: {pot_money} | 争夺者: {eligible} ---")

            # 极端情况：如果这个边池只有一个人有资格接盘（别人钱不够，没跟到底）
            if len(eligible) == 1:
                winner = eligible[0]
                print(f"🎉 只有 [{winner}] 拥有资格，无需比牌，直接收下 {pot_name} 的 {pot_money}！")
                self.state["player_stacks"][winner] += pot_money
                continue

            # 常规情况：多人争夺，调用极速打分器！
            best_score = -1
            winners = []
            player_results = {}

            for p in eligible:
                # 拼凑 7 张牌：2张底牌 + 5张公共牌
                seven_cards = self.dealer.get_physical_hole_cards()[p] + self.dealer.get_physical_community_cards()

                # 👉 呼叫你的 C 级别极速算法
                best_5_cards, (score, mask) = HandEvaluator.get_best_hand(seven_cards)

                # 翻译成人类能看懂的牌型名称 (如果你的类里没有 evaluate_to_str，这行可以直接用 score 代替)
                hand_name = HandEvaluator.evaluate_to_str(score) if hasattr(HandEvaluator,
                                'evaluate_to_str') else f"牌力得分: {score}"

                player_results[p] = {
                    "score": score,
                    "hand_name": hand_name,
                    "best_5": [str(c) for c in best_5_cards]
                }

                print(
                    f"  [{p}] 底牌 {self.state['hole_cards'][p]} ==> 最佳5张: {player_results[p]['best_5']} ({hand_name})")

                # 寻找最高分
                if score > best_score:
                    best_score = score
                    winners = [p]
                elif score == best_score:
                    winners.append(p)  # 遇到同分，加入平局列表

            # 4. 决出胜负，分发奖金
            if len(winners) == 1:
                winner = winners[0]
                print(f"🏆 赢家是 [{winner}]，凭借 【{player_results[winner]['hand_name']}】 拿下 {pot_name}！")
                self.state["player_stacks"][winner] += pot_money
            else:
                # 🤝 处理平局分钱 (Split Pot)
                print(f"🤝 惊天平局！赢家是 {winners}，凭借 【{player_results[winners[0]]['hand_name']}】 平分 {pot_name}！")
                split_amount = pot_money // len(winners)  # 整除防小数
                for w in winners:
                    self.state["player_stacks"][w] += split_amount
                    print(f"   -> [{w}] 分得筹码: {split_amount}")

        # ==========================================
        # 🌟 5. 打印最终财务报表
        # ==========================================
        print("\n" + "📊" * 25)
        print("📈 玩家最新筹码榜：")
        for p in self.players:
            print(f"  - {p}: {self.state['player_stacks'][p]}")
        print("📊" * 25 + "\n")

        # ==========================================
        # ⚔️ 玩家动作执行与校验系统
        # ==========================================
    def process_action(self, player_name: str, action: str, amount: int = 0):
        """
        无情的收银员：处理并校验玩家的动作
        :param action: "FOLD", "CALL", "RAISE", "CHECK"
        :param amount: 只有 RAISE 时需要传入具体加到的金额
        """
        state = self.state
        if state["player_status"][player_name] != "active":
            return  # 死人不能说话

        state["player_acted"][player_name] = True
        stack = state["player_stacks"][player_name]
        current_max = state["current_max_bet"]
        my_bet = state["player_current_bets"][player_name]

        if action == "FOLD":
            state["player_status"][player_name] = "folded"
            state["action_history"].append(f"[{player_name}] 弃牌 (Fold)")

        elif action in ["CALL", "CHECK"]:
            to_call = current_max - my_bet
            if to_call == 0:
                state["action_history"].append(f"[{player_name}] 过牌 (Check)")
            else:
                # 如果手里的钱不够 call，就自动变成 All-in
                actual_call = min(to_call, stack)
                self._deduct_chips(player_name, actual_call)
                if actual_call == stack:
                    state["player_status"][player_name] = "all_in"
                    state["action_history"].append(
                        f"[{player_name}] 筹码不足，全下跟注 (All-in Call) {actual_call}!")
                else:
                    state["action_history"].append(f"[{player_name}] 跟注 (Call) {actual_call}")

        elif action == "RAISE":
            # 加注逻辑：必须大于等于当前最高下注额
            raise_to = max(amount, current_max + state["bb_amount"])  # 最少加一个大盲
            add_amount = raise_to - my_bet
            actual_raise = min(add_amount, stack)

            self._deduct_chips(player_name, actual_raise)

            if actual_raise == stack:
                state["player_status"][player_name] = "all_in"
                state["current_max_bet"] = max(current_max, my_bet + actual_raise)
                state["action_history"].append(
                    f"[{player_name}] 全下加注 (All-in Raise) 到 {my_bet + actual_raise}!")
            else:
                state["current_max_bet"] = raise_to
                state["action_history"].append(f"[{player_name}] 加注 (Raise) 到 {raise_to}")

    def _deduct_chips(self, player_name: str, amount: int):
        """内部辅助：安全扣款并流入底池"""
        self.state["player_stacks"][player_name] -= amount
        self.state["player_current_bets"][player_name] += amount
        self.state["player_total_invested"][player_name] += amount
        self.state["pot"] += amount

        # ==========================================
        # 🔄 游戏流转控制系统 (Betting Loop)
        # ==========================================

    def _play_street(self, stage_name: str):
        """控制单条街的下注流转"""
        print(f"\n{'=' * 40}\n🌊 进入阶段: {stage_name}\n{'=' * 40}")
        self.state["stage"] = stage_name

        # 1. 状态重置：所有人都还没表态
        for p in self.players:
            self.state["player_acted"][p] = False

        # 翻牌后的清理工作 (翻牌前绝对不能清，因为有盲注在里面)
        if stage_name != "Pre-Flop":
            self.state["current_max_bet"] = 0
            for p in self.players:
                self.state["player_current_bets"][p] = 0
            # 翻牌后，游标强制回到小盲位 (SB)
            self._set_first_actor_post_flop()
        self._update_win_rates()

        # ==========================================
        # 🌟 核心死循环：直到所有人钱平齐才退出！
        # ==========================================
        while not self._is_street_resolved():
            current_p = self.players[self.state["current_player_idx"]]

            # 如果玩家已经 All-in 或 弃牌，直接跳过他
            if self.state["player_status"][current_p] != "active":
                self.state["player_acted"][current_p] = True
                self._move_next_player()
                continue

            print(f"\n[引擎] 正在等待 {current_p} 思考与行动...")

            # 🧠 呼叫 AI 大脑获取动
            if self.ai_app:
                # 假设 AI 会返回如: ("RAISE", 100)
                action, amount = self.ai_app.get_decision(self.state, current_p)
            else:
                # 如果没接 AI，默认 Call 兜底，防止死循环
                action, amount = "CALL", 0

            # 💰 无情的收银员：执行动作并扣钱 (调用你上一轮刚写好的 process_action)
            self.process_action(current_p, action, amount)

            # ➡️ 移交话语权给下一个人
            self._move_next_player()

        print(f"🏁 {stage_name} 阶段下注结束！当前底池: {self.state['pot']}")

    def _is_street_resolved(self) -> bool:
        """
        极其严谨的结算判定器：当前街是否可以结束？
        """
        # 1. 真正的提前结束条件：看看桌上还有几个没弃牌的人（包含 active 和 all_in）
        unfolded_players = [p for p in self.players if self.state["player_status"][p] != "folded"]
        if len(unfolded_players) <= 1:
            return True  # 对手全跑了，直接结束收钱

        # 2. 常规结束条件：只检查那些还需要说话的活人
        active_players = [p for p in self.players if self.state["player_status"][p] == "active"]

        max_bet = self.state["current_max_bet"]

        for p in active_players:
            # 只要有一个活人没表态，继续转圈
            if not self.state["player_acted"][p]:
                return False
            # 只要有一个活人的钱没补齐，继续转圈
            if self.state["player_current_bets"][p] < max_bet:
                return False

        return True

    def _move_next_player(self):
        """游标顺时针移动到下一个人"""
        idx = self.state["current_player_idx"]
        self.state["current_player_idx"] = (idx + 1) % len(self.players)

    def _set_first_actor_post_flop(self):
        """翻牌后，找到 SB 位，强制从他开始问话"""
        sb_player = self.dealer.get_player_by_role("SB")
        if sb_player:
            self.state["current_player_idx"] = self.players.index(sb_player)
        else:
            self.state["current_player_idx"] = 0