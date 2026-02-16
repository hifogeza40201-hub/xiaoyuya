# 自动化测试框架实践

## 目录
1. [测试金字塔](#测试金字塔)
2. [pytest 基础](#pytest-基础)
3. [单元测试示例](#单元测试示例)
4. [集成测试示例](#集成测试示例)
5. [Mock 和 Patch](#mock-和-patch)
6. [测试数据库](#测试数据库)
7. [CI/CD 集成](#cicd-集成)

---

## 测试金字塔

```
         /\
        /  \
       / E2E \          端到端测试 (少量)
      /________\
     /          \
    / Integration \     集成测试 (中等)
   /________________\
  /                  \
 /     Unit Tests      \   单元测试 (大量)
/________________________\

运行速度：快 ←————————————→ 慢
稳定性：  高 ←————————————→ 低
成本：   低 ←————————————→ 高
```

**推荐比例**：70% 单元测试 + 20% 集成测试 + 10% E2E 测试

---

## pytest 基础

### 安装

```bash
pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist
pip install factory-boy freezegun responses  # 辅助工具
```

### 配置文件 `pytest.ini`

```ini
[pytest]
# 测试目录
testpaths = tests

# 测试文件模式
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# 标记定义
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (may use database)
    e2e: End-to-end tests (full stack)
    slow: Slow running tests
    api: API tests

# 命令行默认选项
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov

# 异步支持
asyncio_mode = auto

# 过滤器
filterwarnings =
    ignore::DeprecationWarning
```

### 基本用法

```python
# test_basic.py
import pytest


# ============ 基础测试 ============
def test_addition():
    """基础断言测试"""
    assert 1 + 1 == 2


def test_string_contains():
    """字符串断言"""
    text = "hello world"
    assert "world" in text
    assert text.startswith("hello")


# ============ 异常测试 ============
def test_division_by_zero():
    """测试异常抛出"""
    with pytest.raises(ZeroDivisionError):
        1 / 0


def test_value_error_with_message():
    """测试异常消息"""
    with pytest.raises(ValueError, match="must be positive"):
        raise ValueError("value must be positive")


# ============ 参数化测试 ============
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add(a, b, expected):
    """参数化测试 - 运行多组数据"""
    assert a + b == expected


@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("World", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    """字符串大写转换测试"""
    assert input.upper() == expected


# ============ Fixture 基础 ============
@pytest.fixture
def sample_data():
    """基础 fixture - 每次测试都会创建新实例"""
    return {"name": "test", "value": 42}


def test_with_fixture(sample_data):
    """使用 fixture"""
    assert sample_data["name"] == "test"
    assert sample_data["value"] == 42


# ============ 类组织测试 ============
class TestCalculator:
    """测试类 - 相关测试分组"""
    
    def test_add(self):
        assert 1 + 1 == 2
    
    def test_subtract(self):
        assert 3 - 1 == 2
    
    @pytest.mark.skip(reason="暂跳过此测试")
    def test_multiply(self):
        assert 2 * 3 == 6
    
    @pytest.mark.skipif(True, reason="条件跳过")
    def test_divide(self):
        assert 4 / 2 == 2


# ============ 标记使用 ============
@pytest.mark.slow
def test_slow_operation():
    """慢测试标记"""
    import time
    time.sleep(1)
    assert True


@pytest.mark.unit
def test_unit_only():
    """单元测试标记"""
    assert True
```

---

## 单元测试示例

### 1. 计算器类测试

```python
# src/calculator.py
class Calculator:
    """计算器类"""
    
    def add(self, a: float, b: float) -> float:
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, base: float, exponent: float) -> float:
        return base ** exponent


# tests/unit/test_calculator.py
import pytest
from src.calculator import Calculator


class TestCalculator:
    """计算器单元测试"""
    
    @pytest.fixture
    def calc(self):
        """每个测试方法前创建新的计算器实例"""
        return Calculator()
    
    # ============ 加法测试 ============
    def test_add_positive_numbers(self, calc):
        assert calc.add(2, 3) == 5
    
    def test_add_negative_numbers(self, calc):
        assert calc.add(-2, -3) == -5
    
    def test_add_mixed_numbers(self, calc):
        assert calc.add(-2, 3) == 1
    
    def test_add_with_zero(self, calc):
        assert calc.add(5, 0) == 5
    
    def test_add_floats(self, calc):
        result = calc.add(0.1, 0.2)
        assert abs(result - 0.3) < 1e-10  # 浮点数比较
    
    # ============ 除法测试 ============
    def test_divide_normal(self, calc):
        assert calc.divide(10, 2) == 5
    
    def test_divide_by_zero_raises(self, calc):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)
    
    def test_divide_negative(self, calc):
        assert calc.divide(-10, 2) == -5
    
    # ============ 参数化边界测试 ============
    @pytest.mark.parametrize("a,b,expected", [
        (1, 1, 1),      # 小数字
        (1000, 1000, 1000000),  # 大数字
        (0.001, 0.001, 0.000001),  # 小数
        (-1, -1, 1),    # 负负得正
    ])
    def test_multiply_various(self, calc, a, b, expected):
        result = calc.multiply(a, b)
        assert abs(result - expected) < 1e-10
```

### 2. 用户服务测试（带依赖）

```python
# src/user_service.py
from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    email: str
    is_active: bool = True


class UserRepository:
    """用户数据访问层"""
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        raise NotImplementedError
    
    def save(self, user: User) -> User:
        raise NotImplementedError
    
    def delete(self, user_id: int) -> bool:
        raise NotImplementedError


class EmailService:
    """邮件服务"""
    
    def send_welcome_email(self, user: User) -> bool:
        raise NotImplementedError


class UserService:
    """用户业务逻辑层"""
    
    def __init__(self, repository: UserRepository, email_service: EmailService):
        self.repository = repository
        self.email_service = email_service
    
    def get_user(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        return user
    
    def create_user(self, username: str, email: str) -> User:
        if not username or not email:
            raise ValueError("Username and email are required")
        
        user = User(id=0, username=username, email=email)
        saved_user = self.repository.save(user)
        self.email_service.send_welcome_email(saved_user)
        return saved_user
    
    def deactivate_user(self, user_id: int) -> User:
        user = self.get_user(user_id)
        user.is_active = False
        return self.repository.save(user)


# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock, create_autospec
from src.user_service import User, UserService, UserRepository, EmailService


class TestUserService:
    """用户服务单元测试"""
    
    @pytest.fixture
    def mock_repository(self):
        return create_autospec(UserRepository, instance=True)
    
    @pytest.fixture
    def mock_email_service(self):
        return create_autospec(EmailService, instance=True)
    
    @pytest.fixture
    def user_service(self, mock_repository, mock_email_service):
        return UserService(mock_repository, mock_email_service)
    
    @pytest.fixture
    def sample_user(self):
        return User(id=1, username="testuser", email="test@example.com")
    
    # ============ get_user 测试 ============
    def test_get_user_success(self, user_service, mock_repository, sample_user):
        mock_repository.get_by_id.return_value = sample_user
        
        result = user_service.get_user(1)
        
        assert result == sample_user
        mock_repository.get_by_id.assert_called_once_with(1)
    
    def test_get_user_not_found(self, user_service, mock_repository):
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="User 999 not found"):
            user_service.get_user(999)
    
    # ============ create_user 测试 ============
    def test_create_user_success(self, user_service, mock_repository, 
                                  mock_email_service, sample_user):
        mock_repository.save.return_value = sample_user
        mock_email_service.send_welcome_email.return_value = True
        
        result = user_service.create_user("testuser", "test@example.com")
        
        assert result == sample_user
        mock_repository.save.assert_called_once()
        mock_email_service.send_welcome_email.assert_called_once_with(sample_user)
    
    @pytest.mark.parametrize("username,email", [
        ("", "test@example.com"),
        ("testuser", ""),
        (None, "test@example.com"),
        ("testuser", None),
    ])
    def test_create_user_validation(self, user_service, username, email):
        with pytest.raises(ValueError, match="Username and email are required"):
            user_service.create_user(username, email)
    
    # ============ deactivate_user 测试 ============
    def test_deactivate_user(self, user_service, mock_repository, sample_user):
        mock_repository.get_by_id.return_value = sample_user
        deactivated_user = User(id=1, username="testuser", 
                                email="test@example.com", is_active=False)
        mock_repository.save.return_value = deactivated_user
        
        result = user_service.deactivate_user(1)
        
        assert result.is_active is False
        mock_repository.save.assert_called_once()
```

---

## 集成测试示例

### 1. 数据库集成测试

```python
# tests/integration/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from src.database import Base, get_db
from src.main import app


@pytest.fixture(scope="session")
def postgres_container():
    """启动 PostgreSQL 容器"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """创建数据库引擎"""
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """每个测试的事务性会话"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI 测试客户端"""
    from fastapi.testclient import TestClient
    
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

```python
# tests/integration/test_user_api.py
import pytest
from src.models import User


class TestUserAPI:
    """用户 API 集成测试"""
    
    def test_create_user(self, client, db_session):
        response = client.post(
            "/api/users/",
            json={"username": "newuser", "email": "new@example.com"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        
        # 验证数据库
        user = db_session.query(User).filter_by(username="newuser").first()
        assert user is not None
    
    def test_get_user(self, client, db_session):
        # 创建测试数据
        user = User(username="testuser", email="test@example.com")
        db_session.add(user)
        db_session.commit()
        
        response = client.get(f"/api/users/{user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
    
    def test_get_nonexistent_user(self, client):
        response = client.get("/api/users/99999")
        assert response.status_code == 404
```

### 2. Redis 集成测试

```python
# tests/integration/test_cache.py
import pytest
import redis
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="module")
def redis_container():
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture
def redis_client(redis_container):
    client = redis.from_url(redis_container.get_connection_url())
    yield client
    client.flushall()


class TestRedisCache:
    def test_set_and_get(self, redis_client):
        redis_client.set("key", "value")
        assert redis_client.get("key") == b"value"
    
    def test_expiration(self, redis_client):
        redis_client.setex("temp_key", 1, "temp_value")
        assert redis_client.get("temp_key") == b"temp_value"
        import time
        time.sleep(1.1)
        assert redis_client.get("temp_key") is None
```

---

## Mock 和 Patch

```python
# tests/unit/test_mocking.py
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime


class TestMockingPatterns:
    """Mock 和 Patch 用法示例"""
    
    # ============ 基础 Mock ============
    def test_basic_mock(self):
        mock = Mock()
        mock.return_value = 42
        
        result = mock()
        
        assert result == 42
        mock.assert_called_once()
    
    def test_mock_with_spec(self):
        """限制 mock 只能访问指定属性"""
        class MyClass:
            def method1(self): pass
            def method2(self): pass
        
        mock = Mock(spec=MyClass)
        mock.method1.return_value = "result"
        
        assert mock.method1() == "result"
        # mock.undefined_method 会报错
    
    # ============ patch 装饰器 ============
    @patch('requests.get')
    def test_patch_decorator(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "test"}
        
        import requests
        response = requests.get("https://api.example.com")
        
        assert response.status_code == 200
        assert response.json()["data"] == "test"
        mock_get.assert_called_with("https://api.example.com")
    
    # ============ patch 上下文管理器 ============
    def test_patch_context_manager(self):
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1)
            
            from datetime import datetime
            now = datetime.now()
            
            assert now.year == 2024
    
    # ============ patch 多个对象 ============
    @patch('module.function1')
    @patch('module.function2')
    def test_multiple_patches(self, mock_func2, mock_func1):
        """注意：装饰器从内到外应用，参数从后往前"""
        mock_func1.return_value = 1
        mock_func2.return_value = 2
        
        # 测试代码
        pass
    
    # ============ patch.dict 环境变量 ============
    @patch.dict('os.environ', {'API_KEY': 'test-key', 'DEBUG': 'true'})
    def test_patch_environment(self):
        import os
        assert os.environ['API_KEY'] == 'test-key'
        assert os.environ['DEBUG'] == 'true'
    
    # ============ Mock 调用验证 ============
    def test_mock_calls(self):
        mock = Mock()
        
        mock(1, 2)
        mock(a=3, b=4)
        mock.method("arg")
        
        # 验证调用
        mock.assert_any_call(1, 2)
        mock.assert_called_with(a=3, b=4)
        
        # 验证调用次数
        assert mock.call_count == 2
        
        # 获取所有调用
        expected_calls = [call(1, 2), call(a=3, b=4)]
        mock.assert_has_calls(expected_calls, any_order=False)
    
    # ============ 副作用 ============
    def test_mock_side_effect(self):
        mock = Mock()
        
        # 序列返回值
        mock.side_effect = [1, 2, 3]
        assert mock() == 1
        assert mock() == 2
        assert mock() == 3
        
        # 异常抛出
        mock.side_effect = ValueError("error")
        with pytest.raises(ValueError):
            mock()
        
        # 函数调用
        def dynamic_return(x):
            return x * 2
        mock.side_effect = dynamic_return
        assert mock(5) == 10
```

---

## 测试数据库

```python
# tests/conftest.py - 数据库配置
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db


# 内存 SQLite 用于快速单元测试
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


# 使用工厂模式创建测试数据
@pytest.fixture
def user_factory(db_session):
    """用户工厂"""
    def _create_user(username=None, email=None, **kwargs):
        from src.models import User
        user = User(
            username=username or f"user_{id(object())}",
            email=email or f"user_{id(object())}@test.com",
            **kwargs
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user


@pytest.fixture
def post_factory(db_session, user_factory):
    """文章工厂"""
    def _create_post(title=None, content=None, author=None, **kwargs):
        from src.models import Post
        if author is None:
            author = user_factory()
        
        post = Post(
            title=title or f"Post {id(object())}",
            content=content or "Test content",
            author_id=author.id,
            **kwargs
        )
        db_session.add(post)
        db_session.commit()
        db_session.refresh(post)
        return post
    return _create_post
```

---

## CI/CD 集成

```bash
# run_tests.sh - 测试执行脚本
#!/bin/bash
set -e

echo "=== 安装依赖 ==="
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "=== 运行单元测试 ==="
pytest tests/unit -v --cov=src --cov-report=xml -m "not integration and not e2e"

echo "=== 运行集成测试 ==="
pytest tests/integration -v -m integration

echo "=== 生成覆盖率报告 ==="
pytest --cov=src --cov-report=html --cov-report=term-missing

echo "=== 测试完成 ==="
```

