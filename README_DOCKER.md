# Docker + Jenkins 部署指南

## 快速开始

### 本地测试

1. **构建并运行 Docker 容器**:
```bash
# 构建镜像
docker build -t ai-interview-test .

# 运行容器
docker run --rm ai-interview-test
```

2. **使用 docker-compose**:
```bash
# 启动
docker-compose up

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## Jenkins 部署

### 方式一：使用 Jenkinsfile（推荐）

1. 在 Jenkins 创建新的 Pipeline 任务
2. 源码管理选择 Git，填入仓库地址
3. Pipeline 选择 "Jenkinsfile from SCM"
4. 点击构建

### 方式二：Docker 命令

在 Jenkins 的 "Execute shell" 中运行:
```bash
# 构建镜像
docker build -t ai-interview-test .

# 运行测试
docker run --rm \
  -e DB_HOST=$DB_HOST \
  -e DB_PASSWORD=$DB_PASSWORD \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/screenshots:/app/screenshots \
  ai-interview-test
```

---

## 环境变量配置

复制 `.env.example` 为 `.env`:
```bash
cp .env.example .env
```

然后修改配置:
- `DB_HOST` - 数据库主机
- `DB_PASSWORD` - 数据库密码
- `BASE_URL` - 测试环境 URL

---

## 注意事项

⚠️ **重要**: 
1. 数据库地址 `10.11.150.253` 是内网地址，Jenkins 需要能访问
2. 测试 URL `58.60.153.86:57070` 需要网络可达
3. `wav/` 目录下的假视频/音频文件需要存在
