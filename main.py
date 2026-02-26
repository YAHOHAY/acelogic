# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import time

from ai_agent.graph import PokerLangGraphAgent
from engine.game import GameEngine

# 导入我们的核心引擎和 AI 大脑

# ==========================================
# 1. 实例化 FastAPI 应用 (Uvicorn 的唯一入口)
# ==========================================
app = FastAPI(
    title="AceLogic AI Poker Server",
    description="基于 LangGraph 的多智能体德州扑克推演引擎",
    version="2.0.0"
)

# ==========================================
# 2. 全局单例初始化 (性能优化极致体现)
# ==========================================
print("[系统] 正在初始化全局 LangGraph 大脑...")
# 把它放在外面，意味着服务器启动时只连接一次大模型，后续请求直接复用！
global_ai_app = PokerLangGraphAgent()
print("[系统] 全局大脑准备就绪！")


# ==========================================
# 3. 定义前端请求体的数据模型 (Pydantic 校验)
# ==========================================
class GameSimulationRequest(BaseModel):
    initial_stack: int = 500
    # 以后你可以在这里加上 "player_names" 等字段，让前端传参数进来


# ==========================================
# 4. 编写 API 路由接口
# ==========================================

@app.get("/")
def health_check():
    """
    健康检查接口：
    运维常识：Docker 和 K8s (Kubernetes) 极其依赖这种根路径接口来判断容器死没死。
    """
    return {"status": "ok", "message": "AceLogic API 引擎运转正常！准备接受对局请求。"}


@app.post("/api/v1/game/simulate")
def simulate_game(req: GameSimulationRequest):
    """
    核心推演接口：
    接收 HTTP 请求 -> 触发一局完整的多智能体博弈 -> 将最终账本打包成 JSON 返回给调用方。
    注意：这里用 def 而不是 async def，因为我们的 start_game 是同步阻塞代码，
    FastAPI 会极其聪明地把它扔进底层的线程池（Threadpool）里执行，不会卡死主服务器！
    """
    print(f"\n[API 接收请求] 准备开启新的一局，初始筹码: {req.initial_stack}")

    # 1. 配置玩家信息
    players_info = {
        "Alice": "极其激进的紧凶型玩家（TAG）。胜率>70%必加注或All-in。",
        "Bob": "松弱的跟注站（Calling Station）。极度讨厌弃牌。",
        "Charlie": "狡猾的诈唬狂魔（Maniac）。经常在没中牌时重注诈唬。"
    }

    # 2. 实例化本局引擎
    game = GameEngine(
        players_info=players_info,
        ai_app=global_ai_app,
        initial_stack=req.initial_stack
    )

    # 3. 🧨 点火推演！(这里服务器会计算几秒钟，直到大模型把这局打完)
    start_time = time.time()
    game.start_game()
    cost_time = round(time.time() - start_time, 2)

    # 4. 提取最终账本状态
    final_state = game.state

    # 5. 组装 JSON 响应返回给前端或 Postman
    return {
        "status": "success",
        "message": f"牌局推演完成，耗时 {cost_time} 秒",
        "data": {
            "final_pot": final_state["pot"],
            "community_cards": final_state.get("community_cards", []),
            # 展示所有人的最终筹码余额
            "final_stacks": final_state["player_stacks"],
            # 截取最后 15 条动作历史，让前端知道发生了什么
            "action_history": final_state["action_history"][-40:]
        }
    }