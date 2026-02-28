from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from ace_logic.ai_agent.nodes import AgentThinkingState, perception_node, strategy_node, action_node, human_action_node


# ==========================================
# 1. 编排 LangGraph 多步思考回路
# ==========================================
def build_brain_graph():
    workflow = StateGraph(AgentThinkingState)

    # 注册节点
    workflow.add_node("perception", perception_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("action", action_node)
    workflow.add_node("human_action_node", human_action_node)

    # 线性串联思考逻辑：看牌 -> 想对策 -> 做决定
    workflow.add_edge(START, "perception")
    workflow.add_edge("perception", "strategy")
    workflow.add_edge("strategy", "action")
    workflow.add_edge("action", END)
    # 4. 人类节点走完，也直接结束当前图，回到外部世界
    workflow.add_edge("human_action_node", END)
    # 5. 实例化硬盘
    memory = MemorySaver()

    # 6. ⚡ 注入灵魂：编译图，挂载硬盘，并设置物理级断点！
    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_action_node"]
    )


# 编译成全局唯一的大脑应用
ai_brain_app = build_brain_graph()


# ==========================================
# 2. 对外暴露的安全包装类 (适配 GameEngine)
# ==========================================
class PokerLangGraphAgent:
    """包装类：让 GameEngine 极简调用，隐藏内部复杂的 LangGraph 逻辑"""

    def __init__(self):
        self.app = ai_brain_app

    def get_decision(self, table_state: dict, player_name: str,game_id: str) -> tuple[str, int]:
        """引擎只需调这个方法，AI 会在内部走完所有节点"""

        # 1. 组装送进大脑的初始数据
        # ⚡ 新增：定义 LangGraph 的运行时配置 (Config)
        config = {"configurable": {"thread_id": f"game_{game_id}_player_{player_name}"}}
        initial_brain_state = {
            "table_state": table_state,
            "player_name": player_name,
            "call_amount": 0,
            "inner_monologue": "",
            "final_action": "CALL",
            "final_amount": 0
        }

        # 2. 启动图运转 (LangGraph 接管)
        final_brain_state = self.app.invoke(initial_brain_state, config=config)

        # 3. 提取结果，交给引擎去扣钱
        return final_brain_state["final_action"], final_brain_state["final_amount"]