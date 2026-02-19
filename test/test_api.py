from fastapi.testclient import TestClient
from main import app  # 确保这里导入的是你 main.py 里的 app 实例


def test_win_rate_api():
    # 核心魔法：必须使用 `with TestClient(app)` 上下文管理器！
    # 只有这样，FastAPI 才会执行 @asynccontextmanager 里的预热代码（加载扑克查找表）。
    # 如果不写 with，你的测试会因为找不到表而直接报错 500。
    with TestClient(app) as client:
        # 1. 准备给接口发送的“假数据”
        payload = {
            "hole_cards": ["Ah", "Ad"],  # 给测试用例发两张红桃A和方块A
            "community_cards": ["7s", "8s", "9s"],
            "opponent_count": 1,
            "user_name": "Pytest_Robot"
        }

        # 2. 模拟前端，向你的接口发送 POST 请求
        response = client.post("/win_rate", json=payload)

        # 3. 断言 (Assert)：质检员开始核对结果
        # 验证一：HTTP 状态码必须是 200 (成功)
        assert response.status_code == 200

        # 将返回的 JSON 转换为 Python 字典
        data = response.json()

        # 验证二：返回的数据里必须包含胜率字段
        assert "winrate" in data
        assert "hands_per_second" in data

        # 验证三：逻辑断言。AA 面对任意单挑对手，在翻牌圈的胜率绝对不可能低于 50%
        assert data["winrate"] > 0.5

        print("\n✅ API 测试通过！计算出的胜率为:", data["winrate"])