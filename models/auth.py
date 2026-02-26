# ace_logic/models/auth.py

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ==========================================
# 1. 定义所有表的基础类 (Base)
# ==========================================
class Base(DeclarativeBase):
    """所有 SQLAlchemy ORM 模型的基类"""
    pass


# ==========================================
# 2. 核心账户与风控表 (Users)
# ==========================================
class User(Base):
    __tablename__ = "users"

    # 使用 UUID 防爬虫遍历 (面试关键点：绝不用自增 ID 暴露用户量)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # 密码哈希与盐值，绝不存明文
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[str] = mapped_column(String(100), nullable=False)

    # 核心风控维度：0=正常, 1=高危(触发滑动验证码), 99=封禁
    risk_level: Mapped[int] = mapped_column(Integer, default=0, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ORM 关系映射：一个用户可以有多个设备和多条登录日志
    devices: Mapped[list["UserDevice"]] = relationship("UserDevice", back_populates="user",
                                                       cascade="all, delete-orphan")
    login_logs: Mapped[list["LoginLog"]] = relationship("LoginLog", back_populates="user", cascade="all, delete-orphan")


# ==========================================
# 3. 硬件特征与浏览器指纹库 (User Devices)
# ==========================================
class UserDevice(Base):
    __tablename__ = "user_devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    device_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PC / Mobile
    os_info: Mapped[str] = mapped_column(String(100), nullable=True)  # 操作系统

    # 核心字段：前端收集的浏览器或硬件哈希指纹
    browser_fingerprint: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # 信任设备机制（如果换了新电脑登录，is_trusted 为 False，需要邮箱验证）
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ORM 反向映射
    user: Mapped["User"] = relationship("User", back_populates="devices")
    logs: Mapped[list["LoginLog"]] = relationship("LoginLog", back_populates="device")


# ==========================================
# 4. 行为溯源与 AI 算法供弹库 (Login Logs)
# ==========================================
class LoginLog(Base):
    __tablename__ = "login_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_devices.id"), nullable=True)

    # 使用 PostgreSQL 特有的 INET 类型，搜索网段（比如抓同一网吧的黑产机器）极速！
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=True)

    # 状态枚举：SUCCESS, FAILED_PWD, BLOCKED_BY_RISK
    login_status: Mapped[str] = mapped_column(String(20), nullable=False)
    login_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # ORM 反向映射
    user: Mapped["User"] = relationship("User", back_populates="login_logs")
    device: Mapped["UserDevice"] = relationship("UserDevice", back_populates="logs")