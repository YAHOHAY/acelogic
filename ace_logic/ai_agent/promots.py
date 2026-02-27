from typing import Literal, Union
from pydantic import BaseModel, Field, field_validator


# ==========================================
# 1. 强制输出格式约束 (Schema)
# ==========================================
class PokerDecision(BaseModel):
    action: Literal["fold", "call", "raise"] = Field(description="决定: fold, call, raise")
    amount: Union[int, str] = Field(description="下注金额。跟注或弃牌填 0")

    @field_validator("amount", mode="before")
    @classmethod
    def clean_amount(cls, v):
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0


# ==========================================
# 2. 动态 Prompt 生成器
# ==========================================
def build_strategy_prompt(p_name: str, persona: str, t_state: dict, call_amount: int) -> str:
    """节点2：生成战略思考提示词 (终极完整版)"""

    # 1. 安全提取所有核心战略数据
    win_rate = t_state.get('win_rates', {}).get(p_name, 0.0)
    position = t_state.get('player_positions', {}).get(p_name, "未知")
    stack = t_state.get('player_stacks', {}).get(p_name, 0)
    pot = t_state.get('pot', 0)
    stage = t_state.get('stage', '未知')
    history = t_state.get('action_history',"weizhi")
    current_max_bet = t_state.get('current_max_bet', 0)
    # 在组装 prompt 之前算一下
    stack_ratio = (call_amount / stack) * 100 if stack > 0 else 0
    #底池赔率
    pot_odds = (call_amount / (pot + call_amount)) * 100 if pot > 0 else 0




    # 2. 组装极具压迫感的 Prompt
    return f"""
    你是 {p_name}，性格是：{persona}。

    【客观牌局信息】
    当前阶段：{stage}
    行动历史：{history}
    底池大小：{pot}
    公共牌：{t_state.get('community_cards', [])}
    最近的历史动作：{t_state.get('action_history', [])[-4:]}
    f"你的底池赔率是 {pot_odds:.1f}%。这意味着只要你的真实胜率大于底池赔率，跟注在数学上就是稳赚不赔的！"f"【关键警告】：如果你已经在这个底池投入了大量筹码，且你剩余的筹码极少（也就是你被底池套牢了），那么即使胜率低，你也应该无脑跟注 (CALL)！"

    【你的专属情报】
    底牌：{t_state.get('hole_cards', {}).get(p_name, [])}
    位置：{position}
    你的真实胜率：{win_rate * 100:.1f}%
    剩余筹码：{stack}
    面临的下注压力：你需要跟注 {call_amount}。这相当于你剩余筹码的 {stack_ratio:.1f}%！"
    f"【合法加注规则】：当前的最高水位是 {current_max_bet}。如果你想加注 (RAISE)，你的 amount 必须大于等于 {current_max_bet}！否则将被视为违规！"

    请结合你的底池赔率、位置优势和性格，用一句话描述你现在的内心真实想法。
    （示例：这底池太香了，而且我在庄位，虽然胜率一般但我必须诈唬他一手；或者，赔率不划算，虽然我是激进型但现在也只能跑了。）
    """


def build_action_prompt(stack: int, inner_monologue: str) -> str:
    """节点3：生成最终动作提示词"""
    return f"""
    结合你的内心独白："{inner_monologue}"

    请严格输出你的最终决定（JSON）。
    剩余筹码：{stack}。加注绝对不能超过这个数字。
    """