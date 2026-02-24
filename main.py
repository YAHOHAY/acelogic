# main.py
import sys
import time

from ai_agent.graph import PokerLangGraphAgent
from engine.game import GameEngine


# 导入我们的三大模块！


def main():
    print("=" * 60)
    print("♠️ ♥️ 欢迎来到 AceLogic V2.0 多智能体德扑宇宙 ♦️ ♣️")
    print("=" * 60)
    time.sleep(1)

    # 1. 设定这桌的玩家名字和性格 (你可以随便捏脸)
    players_info = {
        "Alice": "极其激进的紧凶型玩家（TAG）。你拿到好牌必定重拳出击，如果胜率超过 70% 你会疯狂加注甚至 All-in。如果你没中牌且面临下注，你会果断弃牌。",
        "Bob": "松弱的跟注站（Calling Station）。你极度讨厌弃牌，只要胜率有个 30%，或者你需要跟注的筹码不多，你就会一直跟注看牌。你很少主动加注。",
        "Charlie": "狡猾的诈唬狂魔（Maniac）。你经常在没中牌、胜率极低（比如 <20%）的时候，假装自己牌很大，强行丢出巨额筹码（Raise）来吓退别人。"
    }

    # 2. 唤醒拥有多步思考回路的 LangGraph 大脑
    print("\n[系统] 正在连接 Groq 大模型并编译 AI 神经网络...")
    ai_app = PokerLangGraphAgent()
    print("[系统] AI 神经网络连接完毕！")
    time.sleep(1)

    # 3. 实例化最高主宰：游戏引擎
    print("[系统] 正在启动 AceLogic 物理与规则引擎...")
    game = GameEngine(
        players_info=players_info,
        ai_app=ai_app,
        initial_stack=2000 # 每个人发 2000 块钱启动资金
    )

    # 4. 🧨 点火！见证奇迹！
    game.start_game()

if __name__ == "__main__":
    main()