import os
from typing import TypedDict
from langchain_groq import ChatGroq

from ai_agent.promots import PokerDecision, build_action_prompt, build_strategy_prompt

# ==========================================
# 0. 初始化大模型 (请填入你的真实 Key)
# ==========================================
os.environ["GROQ_API_KEY"] = ""
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
structured_llm = llm.with_structured_output(PokerDecision)


# ==========================================
# 1. 脑部草稿本状态定义
# ==========================================
class AgentThinkingState(TypedDict):
    """AI 思考时的脑部草稿本，绝对不会污染引擎的 TableState"""
    table_state: dict
    player_name: str

    call_amount: int
    inner_monologue: str
    final_action: str
    final_amount: int


# ==========================================
# 2. 具体执行节点 (Nodes)
# ==========================================
def perception_node(state: AgentThinkingState):
    """👁️ 节点 1：感知与计算压力"""
    p_name = state["player_name"]
    t_state = state["table_state"]

    current_max = t_state["current_max_bet"]
    my_bet = t_state["player_current_bets"][p_name]
    call_amount = current_max - my_bet

    print(f"\n[🧠 {p_name} 的大脑 - 节点1: 感知] 面临下注压力: {call_amount}")
    return {"call_amount": call_amount}


def strategy_node(state: AgentThinkingState):
    """🤔 节点 2：战略分析 (生成内心独白)"""
    p_name = state["player_name"]
    t_state = state["table_state"]
    persona = t_state["personas"].get(p_name, "标准")

    prompt = build_strategy_prompt(p_name, persona, t_state, state["call_amount"])

    # 自由输出一段文本作为“内心独白”
    response = llm.invoke(prompt)
    monologue = response.content

    print(f"[🧠 {p_name} 的大脑 - 节点2: 战略] 内心独白: {monologue}")
    return {"inner_monologue": monologue}


def action_node(state: AgentThinkingState):
    """🔨 节点 3：最终决策 (输出严格 JSON)"""
    p_name = state["player_name"]
    stack = state["table_state"]["player_stacks"][p_name]

    prompt = build_action_prompt(stack, state["inner_monologue"])

    try:
        decision = structured_llm.invoke(prompt)
        action = decision.action.upper()
        amount = decision.amount
        print(f"[🧠 {p_name} 的大脑 - 节点3: 行动] 决定: {action} {amount}")
    except Exception as e:
        print(f"[🚨 AI 崩溃保护] {e}")
        action, amount = ("FOLD" if state["call_amount"] > 0 else "CALL"), 0

    return {"final_action": action, "final_amount": amount}