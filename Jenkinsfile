pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'ai-interview-auto-test'
        PYTHONUNBUFFERED = '1'
        PLAYWRIGHT_BROWSERS_PATH = '/ms-playwright'
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
                echo '代码拉取完成'
            }
        }

        stage('环境检查') {
            steps {
                sh '''
                    echo "=== Docker 版本:" && docker --version
                    echo "=== 当前用户:" && whoami
                    echo "=== 工作空间:" && pwd
                '''
            }
        }

        stage('构建 Docker 镜像') {
            steps {
                sh '''
                    echo "开始构建 Docker 镜像..."
                    docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                    docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest
                    echo "镜像构建完成"
                    docker images | grep ${DOCKER_IMAGE}
                '''
            }
        }

        stage('运行自动化测试') {
            steps {
                sh '''
                    echo "启动自动化测试容器..."
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

                    echo "测试执行完成"
                '''
            }
        }

        stage('查看测试结果') {
            steps {
                sh '''
                    echo "=== 测试日志 ==="
                    ls -la logs/ 2>/dev/null || echo "无日志文件"
                    echo "=== 测试截图 ==="
                    ls -la screenshots/ 2>/dev/null || echo "无截图文件"
                    echo "=== 测试视频 ==="
                    ls -la videos/ 2>/dev/null || echo "无视频文件"
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
