# CI/CD 流程设计与实现

## 目录
1. [GitHub Actions 配置模板](#github-actions)
2. [GitLab CI 配置模板](#gitlab-ci)
3. [CI/CD 最佳实践](#最佳实践)

---

## GitHub Actions

### 1. Python 项目完整 CI/CD 工作流

```yaml
# .github/workflows/python-ci-cd.yml
name: Python CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ created ]

env:
  PYTHON_VERSION: '3.11'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============ 代码质量检查 ============
  lint:
    name: Code Quality Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          
      - name: Install linting tools
        run: |
          pip install flake8 black isort mypy bandit
          
      - name: Run flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        
      - name: Check Black formatting
        run: black --check --diff .
        
      - name: Check import sorting
        run: isort --check-only --diff .
        
      - name: Type check with mypy
        run: mypy src/
        
      - name: Security scan with bandit
        run: bandit -r src/ -f json -o bandit-report.json || true
        
      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json

  # ============ 测试阶段 ============
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
        
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run unit tests with coverage
        run: |
          pytest tests/unit --cov=src --cov-report=xml --cov-report=html -v
          
      - name: Run integration tests
        run: |
          pytest tests/integration -v --tb=short
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
          
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results-${{ matrix.python-version }}
          path: |
            htmlcov/
            junit.xml

  # ============ 构建 Docker 镜像 ============
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test]
    permissions:
      contents: read
      packages: write
      
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

  # ============ 部署到测试环境 ============
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    environment:
      name: staging
      url: https://staging.example.com
    if: github.ref == 'refs/heads/develop'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        uses: azure/setup-kubectl@v3
        
      - name: Set up Helm
        uses: azure/setup-helm@v3
        
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name staging-cluster
        
      - name: Deploy to staging
        run: |
          helm upgrade --install myapp ./helm-chart \
            --namespace staging \
            --set image.tag=${{ github.sha }} \
            --set environment=staging \
            --wait --timeout 5m
            
      - name: Run smoke tests
        run: |
          kubectl run smoke-test --rm -i --restart=Never \
            --image=curlimages/curl \
            -- curl -f https://staging.example.com/health

  # ============ 部署到生产环境 ============
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    environment:
      name: production
      url: https://example.com
    if: github.event_name == 'release'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Deploy to production
        run: |
          helm upgrade --install myapp ./helm-chart \
            --namespace production \
            --set image.tag=${{ github.event.release.tag_name }} \
            --set environment=production \
            --wait --timeout 10m
            
      - name: Notify deployment status
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Production deployment ${{ job.status }}: ${{ github.event.release.tag_name }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 2. Node.js 项目 CI/CD 工作流

```yaml
# .github/workflows/nodejs-ci-cd.yml
name: Node.js CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18.x, 20.x, 21.x]
        
    steps:
      - uses: actions/checkout@v4
      
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run linter
        run: npm run lint
        
      - name: Run tests
        run: npm test -- --coverage
        
      - name: Build application
        run: npm run build
        
      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: build-files-${{ matrix.node-version }}
          path: dist/

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run npm audit
        run: npm audit --audit-level=moderate
        
      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

---

## GitLab CI

### 1. Python 项目完整 `.gitlab-ci.yml`

```yaml
# .gitlab-ci.yml
image: python:3.11-slim

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  DOCKER_REGISTRY: "$CI_REGISTRY"
  DOCKER_IMAGE: "$CI_REGISTRY_IMAGE"

stages:
  - lint
  - test
  - build
  - security
  - deploy

# ============ 缓存配置 ============
cache:
  paths:
    - .cache/pip
    - venv/

# ============ 代码质量检查 ============
flake8:
  stage: lint
  before_script:
    - pip install flake8
  script:
    - flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
  allow_failure: true

black:
  stage: lint
  before_script:
    - pip install black
  script:
    - black --check --diff .

isort:
  stage: lint
  before_script:
    - pip install isort
  script:
    - isort --check-only --diff .

mypy:
  stage: lint
  before_script:
    - pip install mypy
  script:
    - mypy src/

# ============ 测试阶段 ============
unit_tests:
  stage: test
  before_script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install --upgrade pip
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
  script:
    - pytest tests/unit --cov=src --cov-report=xml --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - coverage.xml
    expire_in: 1 week

integration_tests:
  stage: test
  services:
    - postgres:15-alpine
    - redis:7-alpine
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    DATABASE_URL: postgresql://test_user:test_pass@postgres:5432/test_db
    REDIS_URL: redis://redis:6379/0
  before_script:
    - pip install -r requirements.txt
  script:
    - pytest tests/integration -v --tb=short
  only:
    - merge_requests
    - main
    - develop

# ============ 构建阶段 ============
build_docker:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA -t $DOCKER_IMAGE:latest .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA
    - docker push $DOCKER_IMAGE:latest
  only:
    - main
    - tags

# ============ 安全扫描 ============
bandit:
  stage: security
  before_script:
    - pip install bandit
  script:
    - bandit -r src/ -f json -o bandit-report.json || true
    - bandit -r src/ -f screen
  artifacts:
    paths:
      - bandit-report.json
    expire_in: 1 week
    when: always
  allow_failure: true

dependency_check:
  stage: security
  image:
    name: owasp/dependency-check:latest
    entrypoint: [""]
  script:
    - /usr/share/dependency-check/bin/dependency-check.sh
      --project "$CI_PROJECT_NAME"
      --scan .
      --format JSON
      --format HTML
      --out reports/
  artifacts:
    paths:
      - reports/
    expire_in: 1 week
  allow_failure: true

# ============ 部署阶段 ============
deploy_staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context staging
    - helm upgrade --install $CI_PROJECT_NAME ./helm
        --namespace staging
        --set image.tag=$CI_COMMIT_SHA
        --wait
  environment:
    name: staging
    url: https://staging.example.com
  only:
    - develop

deploy_production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context production
    - helm upgrade --install $CI_PROJECT_NAME ./helm
        --namespace production
        --set image.tag=$CI_COMMIT_TAG
        --wait
  environment:
    name: production
    url: https://example.com
  when: manual
  only:
    - tags
```

### 2. 多环境部署模板

```yaml
# .gitlab-ci-template-multi-env.yml
# 多环境部署模板

stages:
  - build
  - test
  - deploy_dev
  - deploy_qa
  - deploy_staging
  - deploy_prod

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE

.docker_login: &docker_login
  - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

.kubectl_config: &kubectl_config
  - kubectl config use-context $KUBE_CONTEXT

# ============ 构建模板 ============
.build_template: &build_definition
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - *docker_login
  script:
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA

# ============ 部署模板 ============
.deploy_template: &deploy_definition
  image: bitnami/kubectl:latest
  before_script:
    - *kubectl_config
  script:
    - helm upgrade --install $CI_PROJECT_NAME ./helm
        --namespace $NAMESPACE
        --set image.tag=$CI_COMMIT_SHA
        --set environment=$ENVIRONMENT
        --wait --timeout 5m

# ============ 实际任务 ============
build:
  <<: *build_definition
  only:
    - merge_requests
    - main
    - develop

develop:
  <<: *deploy_definition
  stage: deploy_dev
  variables:
    KUBE_CONTEXT: dev
    NAMESPACE: development
    ENVIRONMENT: dev
  environment:
    name: development
    url: https://dev.example.com
  only:
    - develop

qa:
  <<: *deploy_definition
  stage: deploy_qa
  variables:
    KUBE_CONTEXT: qa
    NAMESPACE: qa
    ENVIRONMENT: qa
  environment:
    name: qa
    url: https://qa.example.com
  only:
    - merge_requests

staging:
  <<: *deploy_definition
  stage: deploy_staging
  variables:
    KUBE_CONTEXT: staging
    NAMESPACE: staging
    ENVIRONMENT: staging
  environment:
    name: staging
    url: https://staging.example.com
  only:
    - main

production:
  <<: *deploy_definition
  stage: deploy_prod
  variables:
    KUBE_CONTEXT: production
    NAMESPACE: production
    ENVIRONMENT: production
  environment:
    name: production
    url: https://example.com
  when: manual
  only:
    - tags
```

---

## 最佳实践

### 1. 通用原则

```yaml
# 推荐的 workflow 结构
workflow:
  rules:
    # 合并请求时触发
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    # 主分支推送时触发
    - if: $CI_COMMIT_BRANCH == "main"
    # 标签推送时触发
    - if: $CI_COMMIT_TAG
    # 定时触发
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

### 2. 安全最佳实践

- 使用 `secrets` 管理敏感信息
- 启用分支保护规则
- 实施代码审查（至少1个审批）
- 定期轮换密钥
- 使用只读权限的部署密钥

### 3. 性能优化

- 启用缓存（pip, npm, docker layers）
- 使用并行作业
- 优化 Dockerfile（多阶段构建）
- 使用条件执行避免不必要的任务

### 4. 监控与通知

```yaml
# Slack 通知示例
notify:
  stage: notify
  script:
    - |
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Pipeline $CI_PIPELINE_ID completed with status $CI_JOB_STATUS\"}" \
        $SLACK_WEBHOOK_URL
  when: always
```

---

## 快速参考

| 功能 | GitHub Actions | GitLab CI |
|------|----------------|-----------|
| 配置文件 | `.github/workflows/*.yml` | `.gitlab-ci.yml` |
| 环境变量 | `env:` / `secrets` | `variables:` / `CI/CD Variables` |
| 任务并行 | `strategy.matrix` | `parallel: N` |
| 制品存储 | `actions/upload-artifact` | `artifacts:` |
| 缓存 | `actions/cache` | `cache:` |
| 审批 | Environments | `when: manual` |
| 任务模板 | Composite Actions | `&anchors` / `extends` |
