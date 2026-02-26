# ace_logic/models/game.py

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .auth import Base


# ==========================================
# 1. 单局游戏主表 (每一把牌的全局快照)
# ==========================================
class PokerHand(Base):
    __tablename__ = "poker_hands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)  # 所属房间号

    # 最终底池总额
    total_pot: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # 🚀 商业级业务体现：平台抽水 (Rake)
    # 任何商业扑克平台都是靠抽水赚钱的。必须记录这局牌系统抽走了多少钱。
    rake_amount: Mapped[int] = mapped_column(BigInteger, default=0)

    # 最终的公共牌 (如 "5♠,8♥,2♠,3♠,5♣")
    community_cards: Mapped[str] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    players: Mapped[list["HandPlayer"]] = relationship("HandPlayer", back_populates="hand")
    replay: Mapped["HandReplay"] = relationship("HandReplay", back_populates="hand", uselist=False)


# ==========================================
# 2. 玩家单局结果表 (谁赢了？谁输了？谁被抓包了？)
# ==========================================
class HandPlayer(Base):
    __tablename__ = "hand_players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("poker_hands.id"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # 底牌快照
    hole_cards: Mapped[str] = mapped_column(String(20), nullable=False)

    # 这局牌开始时他的筹码量
    initial_stack: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # 🚀 净利润：正数代表赢的钱(扣除抽水后)，负数代表输掉的钱。用于大数据风控算玩家胜率！
    net_profit: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # 是否坚持到了最后亮牌阶段？(用来抓“恶意送筹码”的作弊狗)
    is_showdown: Mapped[bool] = mapped_column(Boolean, default=False)

    hand: Mapped["PokerHand"] = relationship("PokerHand", back_populates="players")


# ==========================================
# 3. 对局动作录像带 (采用 JSONB 实现极其恐怖的读写性能)
# ==========================================
class HandReplay(Base):
    """
    为什么单独拆分一张表？
    因为 action_history 可能非常长。把它和主表 PokerHand 拆开，
    在系统只需要统计“总财务”时，查 PokerHand 极快，不需要加载巨大的 JSON；
    只有玩家点击“回放录像”时，才通过 hand_id 过来拉取这里的 JSONB。
    """
    __tablename__ = "hand_replays"

    hand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("poker_hands.id"), primary_key=True)

    # 🚀 直接把你引擎里的 GameEngine.state["action_history"] 列表整个塞进去！
    # PostgreSQL 底层对 JSONB 有高度优化的 GIN 索引，不仅存得快，甚至还能用 SQL 查：
    # "找出所有在 Turn 阶段选择了 ALL-IN 的录像" -> PG 只需要一句 SQL 就能在 JSON 里查出来！
    actions_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    hand: Mapped["PokerHand"] = relationship("PokerHand", back_populates="replay")