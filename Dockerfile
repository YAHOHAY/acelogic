
# 1. 指定基础镜像：使用官方的 Python 3.11 精简版
FROM python:3.11-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 先把装备清单拷进去，并安装依赖
# (这样做的好处是，只要清单不改，Docker 就会缓存这一步，以后打包飞快)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 把你写的全部代码（包括 hand_lookup.json）拷进容器的 /app 目录
COPY . .

# 5. 暴露 8000 端口
EXPOSE 8000

# 6. 容器启动时执行的命令 (等同于你在终端敲的命令)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]