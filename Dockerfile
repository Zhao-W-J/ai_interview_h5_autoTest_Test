# 使用 Python 官方镜像
FROM python:3.11-slim

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

# 安装系统依赖（Playwright Chromium 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements 并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright Chromium 浏览器（使用国内镜像）
RUN playwright install chromium

# 安装浏览器系统依赖
RUN playwright install-deps chromium

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs screenshots videos traces wav

# 设置默认命令
CMD ["python", "test_interview.py"]
