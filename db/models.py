from sqlalchemy import Column, Integer, String, Float, DateTime, ARRAY
from sqlalchemy.orm import declarative_base
from datetime import datetime

# 定义基类
Base = declarative_base()

class CalculationLog(Base):
    __tablename__ = "calculation_logs"

    id = Column(Integer, primary_key=True, index=True)
    # 记录底牌，用 PostgreSQL 的数组类型，非常方便
    hole_cards = Column(ARRAY(String))
    community_cards = Column(ARRAY(String))
    opponent_count = Column(Integer)
    win_rate = Column(Float)
    hands_per_second = Column(Float) # 记录当时的性能，方便日后吹牛
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Log id={self.id} rate={self.win_rate}>"