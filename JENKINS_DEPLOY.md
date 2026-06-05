# Jenkins 部署自动化测试 - 踩坑记录

本文档记录了将 H5 自动化测试项目部署到 Jenkins 过程中遇到的所有问题和解决方案。

---

## 环境信息

- **服务器**: Linux (Ubuntu)
- **Jenkins**: Docker 容器运行 (`jenkins/jenkins:lts-jdk17`)
- **测试框架**: Playwright + Python
- **代码仓库**: GitHub

---

## 问题清单

### 1. Jenkins 容器无法访问 GitHub

**现象**:
```
fatal: unable to access 'https://github.com/...': Failed to connect to github.com port 443
```

**原因**: Jenkins 容器使用 Docker bridge 网络，网络隔离导致无法访问外网。

**解决方案**: 重启 Jenkins 容器，使用 host 网络模式：
```bash
docker stop jenkins && docker rm jenkins
docker run -d --name jenkins --network host \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker:ro \
  jenkins/jenkins:lts-jdk17
```

---

### 2. Jenkins 容器内没有 Docker 命令

**现象**:
```
docker: not found
```

**原因**: Jenkins 容器只挂载了 Docker socket，没有 Docker 客户端。

**解决方案**: 挂载宿主机 Docker 二进制文件：
```bash
-v /usr/bin/docker:/usr/bin/docker:ro
```

---

### 3. Docker 权限不足

**现象**:
```
permission denied while trying to connect to the docker API
```

**原因**: Jenkins 容器内的用户没有权限访问 Docker socket。

**解决方案**: 修改 Docker socket 权限：
```bash
chmod 666 /var/run/docker.sock
```

---

### 4. Dockerfile 没有被推送到 GitHub

**现象**:
```
unable to prepare context: unable to evaluate symlinks in Dockerfile path: lstat .../Dockerfile: no such file or directory
```

**原因**: Dockerfile 没有被 `git add` 提交。

**解决方案**: 确保所有必要文件都提交到 Git：
```bash
git add Dockerfile docker-compose.yml
git commit -m "Add Docker config"
git push origin main
```

---

### 5. 大文件超过 GitHub 限制

**现象**:
```
error: File wav/face.y4m is 139.70 MB; this exceeds GitHub's file size limit of 100.00 MB
```

**原因**: 视频/音频文件超过 GitHub 限制。

**解决方案**: 从 Git 历史中删除大文件：
```bash
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch wav/*.wav wav/*.y4m screenshots/*.png' \
  --prune-empty --tag-name-filter cat -- --all
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push -f origin main
```

---

### 6. Playwright 浏览器下载超时

**现象**:
```
Error: Request to https://storage.googleapis.com/... timed out after 30000ms
```

**原因**: 服务器访问 Google CDN 超时（国内网络）。

**解决方案**: 
- 方案 A: 使用 Playwright 官方镜像（推荐）
- 方案 B: 配置国内镜像源（不稳定）

---

### 7. pip 安装 Python 依赖慢

**现象**:
```
Downloading playwright-1.60.0-py3-none-manylinux1_x86_64.whl (47.5 MB)
```

**原因**: pip 默认使用国外源，速度慢。

**解决方案**: 在 Dockerfile 中配置国内镜像源：
```dockerfile
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### 8. Playwright 版本与镜像不匹配

**现象**:
```
executable doesn't exist at .../chromium-1217/...
```

**原因**: Docker 镜像 `v1.59.0` 内置的浏览器版本与 `requirements.txt` 中安装的 `playwright==1.60.0` 不匹配。

**解决方案**: 统一版本：
```dockerfile
# Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

# requirements.txt
playwright==1.59.0
pymysql
```

---

### 9. 本地路径在容器中不存在

**现象**:
```
executable_path="C:/Users/zwj/AppData/Local/ms-playwright/..."
```

**原因**: 代码中写死了 Windows 本地路径，容器中不存在。

**解决方案**: 删除 `executable_path`，让 Playwright 自动查找浏览器：
```python
# 删除前
browser = p.chromium.launch(
    executable_path="C:/Users/zwj/...",  # ← 删除
    headless=False
)

# 删除后
browser = p.chromium.launch(headless=False)
```

---

### 10. 本地和 Docker 环境混用

**现象**: 本地能运行，Docker 中报错 `Missing X server or $DISPLAY`

**原因**: 本地用 `headless=False`（有界面），Docker 没有图形界面。

**解决方案**: 用环境变量区分环境：
```python
import os
is_docker = os.getenv('IS_DOCKER', 'false').lower() == 'true'

browser = p.chromium.launch(
    headless=is_docker,  # Docker: True, 本地：False
    args=["--no-sandbox"] if is_docker else []
)
```

Dockerfile 中添加：
```dockerfile
ENV IS_DOCKER=true
```

---

## 最终配置

### Dockerfile
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    IS_DOCKER=true

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs screenshots videos traces wav

CMD ["python", "test_interview.py"]
```

### requirements.txt
```
playwright==1.59.0
pymysql
```

### Jenkinsfile
```groovy
pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'ai-interview-auto-test'
        DB_HOST = '10.11.150.253'
        DB_USER = 'root'
        DB_DATABASE = 'ry-vue-py'
        BASE_URL = 'https://58.60.153.86:57070/h5-digitalHuman?token='
        DB_PASSWORD = credentials('db-password')
    }

    stages {
        stage('拉取代码') {
            steps {
                checkout scm
            }
        }

        stage('环境检查') {
            steps {
                sh 'docker --version'
            }
        }

        stage('构建 Docker 镜像') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
            }
        }

        stage('运行自动化测试') {
            steps {
                sh '''
                    docker run --rm --name ai-interview-test \
                        -e DB_HOST=${DB_HOST} \
                        -e DB_USER=${DB_USER} \
                        -e DB_PASSWORD=${DB_PASSWORD} \
                        -e DB_DATABASE=${DB_DATABASE} \
                        -e BASE_URL=${BASE_URL} \
                        -v $(pwd)/logs:/app/logs \
                        -v $(pwd)/screenshots:/app/screenshots \
                        -v $(pwd)/videos:/app/videos \
                        -v $(pwd)/traces:/app/traces \
                        -v $(pwd)/wav:/app/wav:ro \
                        ${DOCKER_IMAGE}:${BUILD_NUMBER}
                '''
            }
        }

        stage('查看测试结果') {
            steps {
                sh '''
                    ls -la logs/ screenshots/ videos/
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'logs/**, screenshots/**, videos/**, traces/**', allowEmptyArchive: true
            sh 'docker image prune -f'
        }
        success { echo '测试通过！' }
        failure { echo '测试失败！检查日志和截图' }
    }
}
```

---

## 快速排错流程

1. **构建卡住** → 检查网络（镜像拉取、pip 下载）
2. **浏览器启动失败** → 检查 `headless` 设置和 `IS_DOCKER` 环境变量
3. **版本不匹配** → 检查 Docker 镜像版本和 `requirements.txt` 是否一致
4. **权限错误** → 检查 Docker socket 权限
5. **文件找不到** → 检查 Git 是否提交了所有必要文件

---

## 最佳实践总结

1. **使用官方 Playwright 镜像** - 避免浏览器下载问题
2. **固定依赖版本** - 避免版本不匹配
3. **配置国内 pip 源** - 加速依赖安装
4. **用环境变量区分环境** - 兼容本地和 Docker
5. **不要写死本地路径** - 让 Playwright 自动查找浏览器
6. **敏感信息用 Jenkins Credentials** - 不要硬编码密码
