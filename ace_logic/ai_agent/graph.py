from langgraph.graph import StateGraph, START, END

from ace_logic.ai_agent.nodes import AgentThinkingState, perception_node, strategy_node, action_node


# ==========================================
# 1. 编排 LangGraph 多步思考回路
# ==========================================
def build_brain_graph():
    workflow = StateGraph(AgentThinkingState)

    # 注册节点
    workflow.add_node("perception", perception_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("action", action_node)

    # 线性串联思考逻辑：看牌 -> 想对策 -> 做决定
    workflow.add_edge(START, "perception")
    workflow.add_edge("perception", "strategy")
    workflow.add_edge("strategy", "action")
    workflow.add_edge("action", END)

    return workflow.compile()


# 编译成全局唯一的大脑应用
ai_brain_app = build_brain_graph()


# ==========================================
# 2. 对外暴露的安全包装类 (适配 GameEngine)
# ==========================================
class PokerLangGraphAgent:
    """包装类：让 GameEngine 极简调用，隐藏内部复杂的 LangGraph 逻辑"""

    def __init__(self):
        self.app = ai_brain_app

    def get_decision(self, table_state: dict, player_name: str) -> tuple[str, int]:
        """引擎只需调这个方法，AI 会在内部走完所有节点"""

        # 1. 组装送进大脑的初始数据
        initial_brain_state = {
            "table_state": table_state,
            "player_name": player_name,
            "call_amount": 0,
            "inner_monologue": "",
            "final_action": "CALL",
            "final_amount": 0
        }

        # 2. 启动图运转 (LangGraph 接管)
        final_brain_state = self.app.invoke(initial_brain_state)

        # 3. 提取结果，交给引擎去扣钱
        return final_brain_state["final_action"], final_brain_state["final_amount"]