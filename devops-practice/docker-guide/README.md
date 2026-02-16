# Docker 入门指南

## 目录
1. [Docker 基础概念](#docker-基础概念)
2. [Docker 安装](#docker-安装)
3. [Dockerfile 编写](#dockerfile-编写)
4. [Docker Compose 使用](#docker-compose-使用)
5. [Docker 最佳实践](#docker-最佳实践)
6. [实战示例](#实战示例)

---

## Docker 基础概念

### 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **镜像 (Image)** | 只读模板，包含运行应用所需的所有内容 | 类 (Class) |
| **容器 (Container)** | 镜像的运行实例，独立、隔离的进程 | 对象 (Object) |
| **仓库 (Registry)** | 存储和分发镜像的服务 | GitHub |
| **Dockerfile** | 定义镜像构建步骤的文本文件 | 构建脚本 |
| **Volume** | 持久化数据存储，独立于容器生命周期 | 外部硬盘 |
| **Network** | 容器间通信的网络配置 | 虚拟局域网 |

### 容器 vs 虚拟机

```
┌─────────────────────────────────────────┐
│           Virtual Machine               │
│  ┌─────────────────────────────────┐    │
│  │  App A  │  App B  │  App C     │    │
│  ├─────────────────────────────────┤    │
│  │      Bin/Libs (各应用独立)       │    │
│  ├─────────────────────────────────┤    │
│  │      Guest OS (客户机系统)       │    │
│  ├─────────────────────────────────┤    │
│  │      Hypervisor (虚拟化层)       │    │
│  ├─────────────────────────────────┤    │
│  │      Host OS (宿主机系统)        │    │
│  ├─────────────────────────────────┤    │
│  │      Infrastructure (硬件)       │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│           Docker Container              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  App A  │ │  App B  │ │  App C  │   │
│  ├─────────┤ ├─────────┤ ├─────────┤   │
│  │ Bin/Libs│ │ Bin/Libs│ │ Bin/Libs│   │
│  └─────────┘ └─────────┘ └─────────┘   │
│  ├─────────────────────────────────┤   │
│  │      Docker Engine (容器引擎)    │   │
│  ├─────────────────────────────────┤   │
│  │      Host OS (宿主机系统)        │   │
│  ├─────────────────────────────────┤   │
│  │      Infrastructure (硬件)       │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Docker 安装

### Windows / macOS

```bash
# 下载 Docker Desktop
# https://www.docker.com/products/docker-desktop

# 验证安装
docker --version
docker-compose --version

# 测试运行
docker run hello-world
```

### Linux (Ubuntu/Debian)

```bash
# 1. 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 2. 更新 apt 包索引
sudo apt-get update

# 3. 安装依赖
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 4. 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 5. 设置稳定版仓库
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 6. 安装 Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 7. 验证安装
sudo docker run hello-world

# 8. 非 root 用户使用 Docker
sudo usermod -aG docker $USER
newgrp docker
```

---

## Dockerfile 编写

### 基础语法

```dockerfile
# 基础镜像
FROM python:3.11-slim

# 标签信息
LABEL maintainer="your-email@example.com"
LABEL version="1.0"
LABEL description="This is a sample Dockerfile"

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# 工作目录
WORKDIR $APP_HOME

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 多阶段构建（推荐）

```dockerfile
# ==================== 构建阶段 ====================
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==================== 运行阶段 ====================
FROM python:3.11-slim as runner

# 创建非 root 用户
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 只复制必要的文件
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup config/ ./config/

# 切换到非 root 用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["python", "-m", "src.main"]
```

### Node.js 多阶段构建示例

```dockerfile
# ==================== 依赖安装阶段 ====================
FROM node:20-alpine AS dependencies

WORKDIR /app

# 只复制 package 文件以利用缓存
COPY package*.json ./
RUN npm ci --only=production

# ==================== 构建阶段 ====================
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ==================== 运行阶段 ====================
FROM node:20-alpine AS runner

WORKDIR /app

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 只复制生产所需的文件
COPY --from=dependencies /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV NODE_ENV production

CMD ["node", "dist/main.js"]
```

---

## Docker Compose 使用

### 基础配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Web 应用服务
  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner  # 多阶段构建时指定目标
    container_name: myapp-web
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=false
    env_file:
      - .env.production
    volumes:
      - ./static:/app/static:ro
      - media_files:/app/media
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 数据库服务
  db:
    image: postgres:15-alpine
    container_name: myapp-db
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redis123}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: myapp-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_files:/var/www/static:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - backend

  # 后台任务队列 (Celery)
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: myapp-worker
    command: celery -A tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - backend

  # 定时任务调度 (Celery Beat)
  scheduler:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: myapp-scheduler
    command: celery -A tasks beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://localhost:6379/0
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - backend

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  media_files:
    driver: local
  static_files:
    driver: local

networks:
  backend:
    driver: bridge
```

### 开发环境配置

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app  # 挂载代码，支持热重载
      - /app/__pycache__  # 排除缓存目录
    environment:
      - DEBUG=true
      - DATABASE_URL=postgresql://dev:dev@db:5432/devdb
    command: python manage.py runserver 0.0.0.0:8000

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: devdb
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    volumes:
      - postgres_dev:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # 开发工具：MailHog 邮件捕获
  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"  # SMTP 服务器
      - "8025:8025"  # Web 界面

  # 开发工具：Adminer 数据库管理
  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"
    depends_on:
      - db

volumes:
  postgres_dev:
```

---

## Docker 最佳实践

### 1. 镜像优化

```dockerfile
# ✅ 好的做法
FROM python:3.11-slim

# 合并 RUN 命令减少层数
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 使用 .dockerignore 排除不需要的文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ❌ 避免的做法
FROM python:latest  # 使用具体版本标签

RUN apt-get update
RUN apt-get install -y build-essential  # 多个 RUN 命令
RUN apt-get install -y libpq-dev

COPY . .  # 复制所有文件，包括不必要的
RUN pip install -r requirements.txt  # 没有使用 --no-cache-dir
```

### 2. .dockerignore 文件

```
# .dockerignore
# Git
.git
.gitignore
.gitattributes

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build

# Virtual environments
venv/
env/
ENV/
.venv

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Documentation
docs/
*.md
!README.md

# CI/CD
.github/
.gitlab-ci.yml
.travis.yml

# Environment files (可能包含敏感信息)
.env
.env.*
!.env.example

# Docker
Dockerfile*
docker-compose*.yml
.docker/

# Local development
*.log
.DS_Store
```

### 3. 安全实践

```dockerfile
# 使用非 root 用户
FROM python:3.11-slim

# 创建应用用户
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app
COPY --chown=appuser:appgroup . .

# 切换到非 root 用户
USER appuser

CMD ["python", "app.py"]
```

---

## 实战示例

### 快速命令参考

```bash
# ==================== 镜像管理 ====================
# 构建镜像
docker build -t myapp:latest .
docker build -t myapp:1.0 -f Dockerfile.prod .

# 查看镜像
docker images
docker image ls

# 删除镜像
docker rmi myapp:latest
docker image prune  # 删除未使用的镜像

# 标记和推送
docker tag myapp:latest registry.example.com/myapp:1.0
docker push registry.example.com/myapp:1.0

# ==================== 容器管理 ====================
# 运行容器
docker run -d -p 8000:8000 --name myapp myapp:latest
docker run -it --rm ubuntu bash  # 交互式，退出后删除

# 查看容器
docker ps
docker ps -a  # 包括已停止的

# 停止和启动
docker stop myapp
docker start myapp
docker restart myapp

# 进入容器
docker exec -it myapp bash
docker exec -it myapp sh  # 如果没有 bash

# 查看日志
docker logs myapp
docker logs -f myapp  # 实时跟踪
docker logs --tail 100 myapp  # 最后 100 行

# 复制文件
docker cp myapp:/app/file.txt ./local/
docker cp ./local/file.txt myapp:/app/

# ==================== Docker Compose ====================
# 启动服务
docker-compose up
docker-compose up -d  # 后台运行
docker-compose up --build  # 重新构建

# 停止服务
docker-compose down
docker-compose down -v  # 同时删除卷

# 查看状态
docker-compose ps
docker-compose logs
docker-compose logs -f web

# 执行命令
docker-compose exec web bash
docker-compose exec db psql -U user

# 扩展服务
docker-compose up -d --scale worker=3

# ==================== 数据管理 ====================
# 卷管理
docker volume ls
docker volume create mydata
docker volume rm mydata

# 备份数据
docker exec db pg_dump -U user mydb > backup.sql

# 恢复数据
cat backup.sql | docker exec -i db psql -U user mydb

# ==================== 网络管理 ====================
docker network ls
docker network create mynetwork
docker network connect mynetwork container_name
```

### 完整项目结构示例

```
myproject/
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.test.yml
├── .dockerignore
├── .env.example
├── Makefile
├── nginx/
│   ├── nginx.conf
│   └── ssl/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── config.py
├── tests/
│   ├── unit/
│   └── integration/
└── scripts/
    ├── entrypoint.sh
    └── healthcheck.sh
```

