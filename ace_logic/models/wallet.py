# ace_logic/models/wallet.py

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .auth import Base  # 假设 Base 在 auth.py 中定义


# ==========================================
# 1. 核心钱包表 (防高并发扣款覆盖)
# ==========================================
class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)

    # 极度重要：金额绝对不能用 Float！统一用 BigInteger 存储“分”或“最小筹码单位”
    balance: Mapped[int] = mapped_column(BigInteger, default=0)

    # 冻结金额：玩家上桌打牌时，带入的筹码必须先冻结，下桌时再结算
    frozen_amount: Mapped[int] = mapped_column(BigInteger, default=0)

    # 🚀 大厂杀手锏：乐观锁版本号！
    # 当高并发请求同时修改余额时，SQLAlchemy 会自动加上 AND version = X。
    # 如果版本不对会直接抛出 StaleDataError，彻底杜绝“幽灵吞钱”Bug！
    version: Mapped[int] = mapped_column(Integer, default=1)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 告诉 SQLAlchemy 哪个字段是乐观锁
    __mapper_args__ = {"version_id_col": version}

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="wallet")


# ==========================================
# 2. 资金流水账本 (Append-Only，绝对不可修改)
# ==========================================
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallets.id"), index=True, nullable=False)

    # 正数为收入，负数为支出
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # 🚀 审计核心：记录这笔钱变动后的【钱包最终余额快照】
    # 这样半夜财务对账时，只要把 amount 累加，跟 balance_after 对比，瞬间就能查出哪里数据不一致。
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # 流水类型：BUY_IN(买入), CASH_OUT(下桌结算), REWARD(系统奖励) 等
    tx_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 溯源 ID：这笔钱是因为哪一局牌(hand_id)赢的？或者哪个充值订单扣的？
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")