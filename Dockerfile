# 使用 Playwright 官方镜像（已内置 Chromium 和所有依赖）
FROM mcr.microsoft.com/playwright:v1.51.0-jammy

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DB_HOST=10.11.150.253 \
    DB_USER=root \
    DB_PASSWORD=Qwe123!! \
    DB_DATABASE=ry-vue-py \
    BASE_URL=https://58.60.153.86:57070/h5-digitalHuman?token=

# 复制 requirements 并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs screenshots videos traces wav

# 设置默认命令
CMD ["python", "test_interview.py"]
