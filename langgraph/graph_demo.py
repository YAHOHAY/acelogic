import os
from typing import TypedDict, Literal, List, Dict, Union
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq


class AceLogicGame:
    def __init__(self, initial_state: dict):
        self.state = initial_state
        # 这里挂载你手搓的纯后端工具
        # self.deck = Deck()
        # self.evaluator = HandEvaluator()

    def run_hand(self):
        print("\n" + "=" * 50)
        print("🎰 牌局正式开始！")
        print("=" * 50)

        # 1. 翻牌圈 (Flop) - 我们刚才测试的阶段
        self.play_betting_round("翻牌圈 (Flop)")

        # 检查是否所有人都 All-in 或者弃牌了，如果活人不足2个，直接快进！
        if self._count_active_players() >= 2:
            self.deal_community_cards(1)  # 发转牌 (Turn)
            self.play_betting_round("转牌圈 (Turn)")

        if self._count_active_players() >= 2:
            self.deal_community_cards(1)  # 发河牌 (River)
            self.play_betting_round("河牌圈 (River)")

        # 如果前面有人 All-in 导致提前结束下注，荷官要补齐 5 张公共牌
        self._ensure_five_community_cards()

        # 结算阶段！
        self.showdown()

    def play_betting_round(self, stage_name: str):
        print(f"\n--- 🌊 进入 {stage_name} 下注圈 ---")
        self.state["stage"] = stage_name

        # 🌟 极其重要的【清盘动作】：进入新一轮前，重置大家的状态！
        self.state["current_max_bet"] = 0
        for p in self.state["players"]:
            self.state["player_acted"][p] = False
            self.state["player_current_bets"][p] = 0

        # 呼叫你刚刚写好的 LangGraph AI 状态机！
        # AI 咬完一圈后，把最新的状态同步回主引擎
        self.state = app.invoke(self.state)

    def deal_community_cards(self, count: int):
        print(f"\n[后台发牌] 荷官发出了 {count} 张公共牌...")
        # 真实环境：self.state["community_cards"].extend(self.deck.deal(count))
        # 并且这里要调用你的 WinRateCalculator 重新计算每个人的胜率！
        pass

    def _count_active_players(self):
        # 只有 "active" 的人才有资格继续下注，"all_in" 和 "folded" 都不算
        return sum(1 for status in self.state["player_status"].values() if status == "active")

    def _ensure_five_community_cards(self):
        # 处理刚才那种提前 All-in 的情况，直接把桌面的牌补齐到 5 张
        current_len = len(self.state["community_cards"])
        if current_len < 5:
            print(f"\n[后台发牌] 由于玩家 All-in，荷官直接发完剩余的 {5 - current_len} 张公共牌！")
            # 真实环境：self.state["community_cards"].extend(self.deck.deal(5 - current_len))
            self.state["community_cards"].extend(["♣8", "♥9"])  # Mock 发牌

    def showdown(self):
        print("\n" + "💰" * 25)
        print("🏆 进入最终摊牌结算 (Showdown)！")
        print(f"最终公共牌：{self.state['community_cards']}")
        print(f"最终总底池：{self.state['pot']}")
        # 接下来就要调用你的 HandEvaluator 来判定谁赢了，以及处理变态的边池了！
        print("💰" * 25 + "\n")
# ==========================================
# 🔑 在这里填入你的 Groq Key (gsk_开头)
# ==========================================
os.environ["GROQ_API_KEY"] = ""

llm = ChatGroq(
    api_key=os.environ["GROQ_API_KEY"],
    model="llama-3.3-70b-versatile"
)


# === 🌟 核心新增：定义强制输出格式 (Schema) ===
class PokerDecision(BaseModel):
    action: Literal["fold", "call", "raise"] = Field(description="你的决定")
    # 允许它输出字符串或者整数
    amount: Union[int, str] = Field(description="下注金额。跟注或弃牌填 0")
    reason: str = Field(description="你的内在逻辑")

    # 🌟 护盾：大模型如果手贱发了字符串 "0"，我们在这里静默把它转成数字 0
    @field_validator("amount", mode="before")
    @classmethod
    def clean_amount(cls, v):
        try:
            return int(v) # 强转为整数
        except (ValueError, TypeError):
            return 0      # 转换失败直接按 0 处理


# 给 LLM 绑定这个强制格式！
structured_llm = llm.with_structured_output(PokerDecision)


# ==========================================

# 1. 定义状态 (State)
class TableState(TypedDict):
    # ==========================================
    # 一、 全局公共状态 (Global Table Info)
    # ==========================================
    stage: str  # 当前发牌阶段 ("Pre-Flop", "Flop", "Turn", "River") - 比数字 turn 更清晰
    pot: int  # 总底池金额
    community_cards: List[str]  # 公共牌，例如: ["Qs", "Js", "Ts"]
    current_max_bet: int  # 【新增】当前这一轮的最高下注额。用来计算玩家还需要补多少钱
    action_history: List[str]  # 桌面历史动作，供大模型阅读上下文
    # 🌟 【新增】盲注与底注结构！让 AI 知道目前的通货膨胀水平
    sb_amount: int  # 小盲注金额 (如: 10)
    bb_amount: int  # 大盲注金额 (如: 20)
    ante: int  # 底注金额 (如: 0 或 5)

    # ==========================================
    # 二、 玩家公共画像 (Public Roster Info)
    # ==========================================
    players: List[str]  # 玩家出场顺序名单，例如: ["Alice", "Bob", "Charlie"]
    current_player_idx: int  # 当前该谁说话了 (游标)

    player_positions: Dict[str, str]  # 【新增】极其重要！位置映射，例如: {"Alice": "SB", "Bob": "BB", "Charlie": "BTN"}
    player_stacks: Dict[str, int]  # 【新增】玩家当前剩余筹码量！例如: {"Alice": 1000, "Bob": 500}
    player_status: Dict[str, str]  # 【新增】玩家存活状态！("active"-活跃, "folded"-已弃牌, "all_in"-已全下)
    player_current_bets: Dict[str, int]  # 【新增】本轮玩家已经下注的金额。(用来算真实跟注额)
    player_acted: Dict[str, bool]  # 记录本轮下注圈中，每个玩家是否已经采取过行动

    # ==========================================
    # 三、 AI 私有数据 (Private / Hidden Info)
    # = 注意：以下数据是 AceLogic 后台算出来，精准喂给对应 AI 的
    # ==========================================
    hole_cards: Dict[str, List[str]]  # 【修改】从单列表变成字典！{"Alice": ["As", "Kd"], "Bob": ["2c", "7o"]}
    win_rates: Dict[str, float]  # 【修改】每个玩家此时的真实胜率！{"Alice": 0.65, "Bob": 0.12}
    personas: Dict[str, str]  # 每个玩家的性格设定


# ==========================================
# 节点 1：荷官节点 (Dealer Node)
# ==========================================
def dealer_node(state: TableState):
    # 在这个阶段，荷官主要负责推进游戏阶段（比如发公共牌），
    # 真实应用中，这里会调用你的发牌算法和胜率计算器。
    print(f"\n{'=' * 50}")
    print(f"[荷官] 进入 {state['stage']} 阶段！当前底池: {state['pot']}，桌面最高下注: {state['current_max_bet']}")
    print(f"[荷官] 公共牌面: {state['community_cards']}")
    print(f"{'=' * 50}")

    # 荷官宣告完毕，不改变实质性状态，直接进入玩家轮转
    return state


# ==========================================
# 节点 2：玩家节点 (Player Node) - 核心大脑！
# ==========================================
def player_node(state: TableState):
    # 1. 确定当前是谁在行动
    real_idx = state["current_player_idx"] % len(state["players"])
    name = state["players"][real_idx]
    status = state["player_status"][name]

    # 🛑 拦截器：如果玩家已经弃牌或全下，直接跳过他！
    if status in ["folded", "all_in"]:
        new_acted = dict(state["player_acted"])
        new_acted[name] = True
        print(f"[系统] {name} 状态为 '{status}'，已自动跳过。")
        return {
            "current_player_idx": state["current_player_idx"] + 1,
            "player_acted": new_acted
        }

    # 2. 精准提取属于该玩家的私有/公共数据
    hole_cards = state["hole_cards"][name]
    win_rate = state["win_rates"][name]
    stack = state["player_stacks"][name]
    position = state["player_positions"][name]
    persona = state["personas"][name]

    # 🧮 算账：计算他还需要补多少钱才能继续玩 (Pot Odds 的核心)
    already_bet = state["player_current_bets"][name]
    call_amount = state["current_max_bet"] - already_bet

    print(f"\n[系统] 👉 轮到 {name} ({position}位) | 筹码: {stack} | 需要跟注: {call_amount}")

    # 3. 组装极度专业的 Prompt (注入灵魂)
    prompt = f"""
    你是德州扑克玩家 {name}。
    【你的极度性格设定】：{persona}

    【全局绝对事实】：
    - 阶段：{state['stage']}
    - 公共牌：{state['community_cards']}
    - 总底池：{state['pot']}
    - 历史动作（极其重要）：{state['action_history']}

    【你的私有情报】：
    - 位置：{position}
    - 剩余筹码：{stack}
    - 你的手牌：{hole_cards}
    - 当前面临的跟注额：{call_amount} （当前桌上最高下注是 {state['current_max_bet']}，你之前已下注 {already_bet}）
    - 你的后台数学胜率：{win_rate * 100}%


    请基于以上信息做出决策。注意：
    1. 你的加注(raise)金额绝对不能超过你的剩余筹码 {stack}！
    2. 如果你选择跟注(call)，你的 amount 必须填 0（因为跟注的金额系统会自动扣除）。
    3. 如果你选择弃牌(fold)，你的 amount 必须填 0。
    4. 如果你是诈唬，请在 reason 里写明。
    """

    # ==========================================
    # 4. 🧠 大脑推断层：带异常护盾的 LLM 调用
    # ==========================================
    print("[系统] 等待大模型推理中...")
    try:
        # 尝试调用大模型
        decision = structured_llm.invoke(prompt)
        action = decision.action
        raise_amount = decision.amount
        reason = decision.reason
    except Exception as e:
        # 【护盾】如果 Groq 抽风、断网或输出格式炸了，绝不让程序崩溃！
        print(f"\n[🚨 警告] AI 大脑连接异常，强制执行安全动作。错误原因: {e}")
        # 安全降级策略：如果有人下注，就弃牌；如果没人下注，就过牌。
        action = "fold" if call_amount > 0 else "call"
        raise_amount = 0
        reason = "AI 宕机，AceLogic 后台接管，执行安全默认动作"

    print(f"\n[{name} 的原始指令]: {action.upper()} | 意图加注: {raise_amount} | 理由: {reason}")

    # ==========================================
    # 5. 🛠️ Python 严谨逻辑层：金融级筹码结算与规则纠正
    # ==========================================
    # 复制状态字典，确保纯函数特性，不污染老数据
    new_pot = state["pot"]
    new_max_bet = state["current_max_bet"]
    new_history = list(state["action_history"])
    new_stacks = dict(state["player_stacks"])
    new_current_bets = dict(state["player_current_bets"])
    new_status = dict(state["player_status"])

    actual_cost = 0  # 玩家本次动作【实际】需要从口袋里掏出的筹码
    final_action_str = ""  # 记录到历史中的最终合法动作

    # --- 逻辑分支 A：弃牌 (Fold) ---
    if action == "fold":
        # 边界纠正：如果当前需要跟注的钱是 0，说明没人下注，此时不应该 Fold，而是 Check（过牌）
        if call_amount == 0:
            actual_cost = 0
            final_action_str = "过牌 (Check)"
            # 状态不变，玩家依然存活
        else:
            actual_cost = 0
            new_status[name] = "folded"
            final_action_str = "弃牌 (Fold)"

    # --- 逻辑分支 B：跟注 (Call) ---
    elif action == "call":
        actual_cost = min(call_amount, stack)  # 最多只能掏出全部身家

        if actual_cost == 0:
            final_action_str = "过牌 (Check)"
        elif actual_cost == stack:
            final_action_str = f"全下跟注 (All-in Call) 掏出 {actual_cost}"
            new_status[name] = "all_in"
        else:
            final_action_str = f"跟注 (Call) 掏出 {actual_cost}"

    # --- 逻辑分支 C：加注 (Raise) ---
    elif action == "raise":
        # 意图总花费 = 需要补齐的差价(call_amount) + 额外加注的金额(raise_amount)
        intended_cost = call_amount + raise_amount
        actual_cost = min(intended_cost, stack)  # 防御 AI 虚空打钱

        # 边界纠正：如果 AI 算错钱，实际掏出来的钱连“跟注”都不够，或者加注额为 0
        if actual_cost <= call_amount:
            # 强制降级为跟注逻辑
            actual_cost = min(call_amount, stack)
            if actual_cost == stack:
                final_action_str = f"资金不足以加注，被迫全下跟注 (All-in Call) 掏出 {actual_cost}"
                new_status[name] = "all_in"
            else:
                final_action_str = f"无效加注(金额过小)，降级为跟注 (Call) 掏出 {actual_cost}"
        else:
            # 合法的加注 (或 All-in Raise)
            if actual_cost == stack:
                final_action_str = f"全下加注 (All-in Raise) 掏出 {actual_cost}"
                new_status[name] = "all_in"
            else:
                final_action_str = f"加注 (Raise) 掏出 {actual_cost}"

            # 🚨 极度重要：只有合法加注，才能刷新本轮桌面的“最高下注额”指标！
            new_max_bet = already_bet + actual_cost

    # --- 统一执行资产划转 ---
    new_stacks[name] -= actual_cost
    new_current_bets[name] += actual_cost
    new_pot += actual_cost

    # 记录到历史总线上，让下一个玩家能看到这个被纠正过的合法动作
    new_history.append(f"{name} 执行了 {final_action_str}")
    print(f"[{name} 的最终结算]: {final_action_str} | 剩余筹码: {new_stacks[name]}\n")
    new_acted = dict(state["player_acted"])
    new_acted[name] = True  # 当前玩家行动完毕，打上勾

    # 如果玩家加注了 (即刷新了桌面最高下注额)，那么其他人的表态全部作废！
    if new_max_bet > state["current_max_bet"]:
        for p in state["players"]:
            if p != name and state["player_status"][p] == "active":
                new_acted[p] = False  # 剥夺其他活跃玩家的表态标志，逼他们再走一圈

    # 最后返回时，把 new_acted 一起返回更新

    # 6. 将更新后的数据打包返回，LangGraph 会接管并覆盖 State
    return {
        "pot": new_pot,
        "current_max_bet": new_max_bet,
        "action_history": new_history,
        "player_stacks": new_stacks,
        "player_current_bets": new_current_bets,
        "player_status": new_status,
        "player_acted": new_acted,  # 【新增】返回更新后的表态记录
        "current_player_idx": state["current_player_idx"] + 1  # 游标永远无脑向前走
    }


# ==========================================
# 6. 裁判节点 (路由器)：决定是否进入下一位玩家
# ==========================================
def judge_next_player(state: TableState) -> str:
    # 谁还在牌桌上？(只要没 Fold 就算)
    unfolded_players = [p for p, status in state["player_status"].items() if status != "folded"]

    # 极端情况 1：所有人都 Fold 了，只剩 1 个人。他直接赢，提前结束。
    if len(unfolded_players) <= 1:
        print("\n[裁判] 对手全部弃牌，无需继续下注。")
        return END

    # 获取还需要做决策的活跃玩家
    active_players = [p for p, status in state["player_status"].items() if status == "active"]

    # 极端情况 2：如果已经没有活跃玩家了（大家要么 Fold 要么 All-in），直接结束
    if len(active_players) == 0:
        print("\n[裁判] 所有玩家均已全下或弃牌，直接进入发牌结算！")
        return END

    # 常规判断：所有【还在活动的玩家】是否都表态了，且钱平齐了？
    all_acted = all(state["player_acted"][p] for p in active_players)
    all_bets_matched = all(state["player_current_bets"][p] == state["current_max_bet"] for p in active_players)

    # 🌟 核心修复：即使只有 1 个 active 玩家，只要他面临别人的 All-in 且钱还没平齐，就绝不能结束！
    if all_acted and all_bets_matched:
        print("\n[裁判] ✅ 所有活跃玩家均已表态且筹码平齐！本轮下注圈圆满结束。")
        return END
    else:
        return "player"


# ==========================================
# 7. 构建与编译 LangGraph 状态机
# ==========================================
workflow = StateGraph(TableState)

# 添加节点
workflow.add_node("dealer", dealer_node)
workflow.add_node("player", player_node)

# 定义流转边
workflow.add_edge(START, "dealer")  # 游戏开始 -> 荷官发牌宣布信息
workflow.add_edge("dealer", "player")  # 荷官说完 -> 交给第一个玩家思考
workflow.add_conditional_edges("player", judge_next_player)  # 玩家思考完 -> 裁判决定给下一个玩家还是结束

# 编译成可执行的程序
app = workflow.compile()

# ==========================================
# 8. 🚀 引擎点火：注入史诗级 Mock 数据
# ==========================================
if __name__ == "__main__":
    print("=== AceLogic 多智能体性格博弈测试 (终极精细版) ===")

    initial_state = {
        "stage": "翻牌圈 (Flop)",
        "pot": 150,
        "community_cards": ["♠A", "♥K", "♦7"],
        "current_max_bet": 50,
        "action_history": ["翻牌前：众人平跟入池，当前底池 150"],

        "players": ["Alice", "Bob", "Charlie"],
        "current_player_idx": 0,
        "player_positions": {"Alice": "SB (小盲)", "Bob": "BB (大盲)", "Charlie": "BTN (庄位)"},
        "player_stacks": {"Alice": 1000, "Bob": 300, "Charlie": 2000},
        "player_status": {"Alice": "active", "Bob": "active", "Charlie": "active"},
        "player_current_bets": {"Alice": 0, "Bob": 0, "Charlie": 0},

        # 👇 就是漏了这极其关键的一行！点火时大家都没表态
        "player_acted": {"Alice": False, "Bob": False, "Charlie": False},

        "hole_cards": {
            "Alice": ["♣A", "♦A"],
            "Bob": ["♠7", "♣7"],
            "Charlie": ["♠2", "♣7"]
        },
        "win_rates": {
            "Alice": 0.95,
            "Bob": 0.04,
            "Charlie": 0.01
        },
        "personas": {
            # ... (保持你之前的性格描述不变)
            "Alice": "极其紧凶（TAG）的职业老手...",
            "Bob": "松弱（Calling Station）的娱乐玩家...",
            "Charlie": "极其激进的疯子（Maniac）..."
        }
    }

    # 启动牌局
    app.invoke(initial_state)