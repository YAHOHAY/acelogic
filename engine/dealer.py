from ace_logic.core.deck import Deck
from engine.state import TableState


class Dealer:
    def __init__(self, state: TableState):
        self.state = state
        self.deck = Deck()
        # 荷官私藏的真实物理牌对象 (不给 AI 看，结算时才拿出来比大小)
        self._private_hole_cards = {p: [] for p in self.state["players"]}
        self._private_community_cards = []


    def assign_positions(self, btn_idx: int):
        """分配座位，并写入全局状态"""
        players = self.state["players"]
        n = len(players)
        if n < 2:
            self.state["player_positions"] = {players[0]: "BTN"}
            return

        # 动态计算座位
        if n == 2:
            roles = ["BTN/SB", "BB"]
            sb_idx = btn_idx
        else:
            sb_idx = (btn_idx + 1) % n
            if n == 3:
                roles = ["SB", "BB", "BTN"]
            elif n == 4:
                roles = ["SB", "BB", "UTG", "BTN"]
            elif n == 5:
                roles = ["SB", "BB", "UTG", "CO", "BTN"]
            elif n == 6:
                roles = ["SB", "BB", "UTG", "MP", "CO", "BTN"]
            else:
                fillers = [f"MP{i}" for i in range(1, n - 3)] + ["CO"]
                roles = ["SB", "BB", "UTG"] + fillers + ["BTN"]

        position_map = {}
        for physical_idx, player_name in enumerate(players):
            role_idx = (physical_idx - sb_idx) % n
            position_map[player_name] = roles[role_idx]

        self.state["player_positions"] = position_map

    def get_player_by_role(self, target_role: str):
        """辅助方法：根据角色找人"""
        for player_name, role in self.state["player_positions"].items():
            if role == target_role or (target_role == "SB" and role == "BTN/SB"):
                return player_name
        return None

    def collect_blinds_ante(self, sb_amount: int, bb_amount: int, ante :int):
        players = self.state["players"]
        if ante > 0 :
            for p in players:
                stack = self.state["player_stacks"][p]
                ante = min(stack, ante)
                self.state["player_total_invested"][p] += ante
                self.state["player_stacks"][p] -= ante
                self.state["pot"] += ante

        """强制扣除大小盲注"""
        sb_player = self.get_player_by_role("SB")
        bb_player = self.get_player_by_role("BB")

        if sb_player:
            actual_sb = min(sb_amount, self.state["player_stacks"][sb_player])
            self.state["player_total_invested"][sb_player] += actual_sb
            self.state["player_stacks"][sb_player] -= actual_sb
            self.state["player_current_bets"][sb_player] += actual_sb
            self.state["pot"] += actual_sb

        if bb_player:
            actual_bb = min(bb_amount, self.state["player_stacks"][bb_player])
            self.state["player_total_invested"][bb_player] += actual_bb
            self.state["player_stacks"][bb_player] -= actual_bb
            self.state["player_current_bets"][bb_player] += actual_bb
            self.state["pot"] += actual_bb
            self.state["current_max_bet"] = actual_bb
        bb_player = self.get_player_by_role("BB")
        if bb_player:
            bb_idx = self.state["players"].index(bb_player)
            first_actor_idx = (bb_idx + 1) % len(self.state["players"])
            self.state["current_player_idx"] = first_actor_idx
        else:
            self.state["current_player_idx"] = 0

    def deal_hole_cards(self):
        """给每位存活玩家发 2 张底牌"""
        for p in self.state["players"]:
            if self.state["player_status"][p] == "active":
                cards = self.deck.deal(2)
                self._private_hole_cards[p] = cards
                # 把字符串版本写进账本，方便后续 AI 读取
                self.state["hole_cards"][p] = [str(c) for c in cards]

    def deal_community_cards(self, count: int):
        """发公共牌"""
        cards = self.deck.deal(count)
        self._private_community_cards.extend(cards)
        self.state["community_cards"] = [str(c) for c in self._private_community_cards]

    def get_physical_hole_cards(self):
            """向引擎上交所有人的真实物理底牌"""
            return self._private_hole_cards

    def get_physical_community_cards(self):
            """向引擎上交真实的公共牌"""
            return self._private_community_cards


