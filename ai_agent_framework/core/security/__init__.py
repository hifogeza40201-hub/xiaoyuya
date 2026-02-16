from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json
import hashlib
from pathlib import Path


class Permission(Enum):
    """权限类型"""
    TOOL_EXECUTE = "tool_execute"           # 执行工具
    TOOL_REGISTER = "tool_register"         # 注册工具
    MEMORY_READ = "memory_read"             # 读取记忆
    MEMORY_WRITE = "memory_write"           # 写入记忆
    MEMORY_DELETE = "memory_delete"         # 删除记忆
    AGENT_CREATE = "agent_create"           # 创建Agent
    AGENT_DELETE = "agent_delete"           # 删除Agent
    NETWORK_ACCESS = "network_access"       # 网络访问
    FILE_READ = "file_read"                 # 文件读取
    FILE_WRITE = "file_write"               # 文件写入
    CODE_EXECUTE = "code_execute"           # 代码执行
    SANDBOX_ESCAPE = "sandbox_escape"       # 退出沙箱


class Role(Enum):
    """用户角色"""
    ADMIN = "admin"             # 管理员 - 全部权限
    OPERATOR = "operator"       # 操作员 - 大部分权限
    USER = "user"               # 普通用户 - 有限权限
    GUEST = "guest"             # 访客 - 只读权限


@dataclass
class AccessPolicy:
    """访问策略"""
    role: Role
    allowed_permissions: Set[Permission]
    allowed_tools: Optional[Set[str]] = None  # None表示全部
    denied_tools: Set[str] = None
    rate_limit_per_minute: int = 60
    max_tokens_per_request: int = 4000
    
    def __post_init__(self):
        if self.denied_tools is None:
            self.denied_tools = set()


# 预定义角色权限
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.TOOL_EXECUTE, Permission.TOOL_REGISTER,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE, Permission.MEMORY_DELETE,
        Permission.AGENT_CREATE, Permission.AGENT_DELETE,
        Permission.NETWORK_ACCESS, Permission.FILE_READ, Permission.FILE_WRITE,
        Permission.CODE_EXECUTE, Permission.SANDBOX_ESCAPE
    },
    Role.OPERATOR: {
        Permission.TOOL_EXECUTE,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE,
        Permission.AGENT_CREATE,
        Permission.NETWORK_ACCESS, Permission.FILE_READ,
        Permission.CODE_EXECUTE
    },
    Role.USER: {
        Permission.TOOL_EXECUTE,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE,
        Permission.FILE_READ
    },
    Role.GUEST: {
        Permission.MEMORY_READ
    }
}


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.policies: Dict[str, AccessPolicy] = {}  # user_id -> policy
        self._default_role = Role.USER
    
    def set_user_policy(self, user_id: str, policy: AccessPolicy):
        """设置用户策略"""
        self.policies[user_id] = policy
    
    def create_default_policy(self, role: Role) -> AccessPolicy:
        """创建默认策略"""
        return AccessPolicy(
            role=role,
            allowed_permissions=ROLE_PERMISSIONS[role]
        )
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission
    ) -> bool:
        """检查权限"""
        policy = self.policies.get(user_id)
        if not policy:
            # 使用默认策略
            policy = self.create_default_policy(self._default_role)
        
        return permission in policy.allowed_permissions
    
    def check_tool_permission(
        self,
        user_id: str,
        tool_name: str
    ) -> bool:
        """检查工具权限"""
        policy = self.policies.get(user_id)
        if not policy:
            return True
        
        # 检查是否在拒绝列表
        if tool_name in policy.denied_tools:
            return False
        
        # 检查是否在允许列表
        if policy.allowed_tools is not None:
            return tool_name in policy.allowed_tools
        
        return True
    
    def require_permission(self, user_id: str, permission: Permission):
        """装饰器：要求特定权限"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.check_permission(user_id, permission):
                    raise PermissionError(
                        f"User '{user_id}' lacks permission: {permission.value}"
                    )
                return func(*args, **kwargs)
            return wrapper
        return decorator


class AuditLogger:
    """
    审计日志记录器
    
    记录所有重要操作供审计和追踪
    """
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.current_log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        self.events: List[Dict[str, Any]] = []
    
    def log(
        self,
        event_type: str,
        user_id: str,
        action: str,
        details: Dict[str, Any] = None,
        result: str = "success",
        ip_address: str = None
    ):
        """记录事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "result": result,
            "ip_address": ip_address,
            "event_id": self._generate_event_id(event_type, user_id, action)
        }
        
        self.events.append(event)
        self._write_to_file(event)
    
    def log_tool_execution(
        self,
        user_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any,
        duration_ms: float
    ):
        """记录工具执行"""
        self.log(
            event_type="tool_execution",
            user_id=user_id,
            action=f"execute_tool:{tool_name}",
            details={
                "tool": tool_name,
                "parameters": self._sanitize_parameters(parameters),
                "duration_ms": duration_ms
            },
            result="success" if result else "failure"
        )
    
    def log_memory_access(
        self,
        user_id: str,
        operation: str,  # read/write/delete
        memory_type: str,
        content_preview: str = None
    ):
        """记录记忆访问"""
        self.log(
            event_type="memory_access",
            user_id=user_id,
            action=f"memory_{operation}",
            details={
                "memory_type": memory_type,
                "content_preview": content_preview[:100] if content_preview else None
            }
        )
    
    def log_security_event(
        self,
        user_id: str,
        event: str,
        severity: str = "warning",
        details: Dict[str, Any] = None
    ):
        """记录安全事件"""
        self.log(
            event_type="security",
            user_id=user_id,
            action=event,
            details={details},
            result=severity
        )
    
    def query(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询日志"""
        results = self.events
        
        if user_id:
            results = [e for e in results if e["user_id"] == user_id]
        
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        
        if start_time:
            results = [
                e for e in results
                if datetime.fromisoformat(e["timestamp"]) >= start_time
            ]
        
        if end_time:
            results = [
                e for e in results
                if datetime.fromisoformat(e["timestamp"]) <= end_time
            ]
        
        return results[-limit:]
    
    def generate_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """生成审计报告"""
        events = self.query(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # 统计
        event_types = {}
        user_activity = {}
        tool_usage = {}
        
        for event in events:
            # 事件类型统计
            et = event["event_type"]
            event_types[et] = event_types.get(et, 0) + 1
            
            # 用户活动统计
            uid = event["user_id"]
            user_activity[uid] = user_activity.get(uid, 0) + 1
            
            # 工具使用统计
            if et == "tool_execution":
                tool = event["details"].get("tool", "unknown")
                tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        return {
            "period": {
                "start": start_time.isoformat() if start_time else "all",
                "end": end_time.isoformat() if end_time else "all"
            },
            "total_events": len(events),
            "event_types": event_types,
            "user_activity": user_activity,
            "tool_usage": tool_usage,
            "security_events": len([
                e for e in events if e["event_type"] == "security"
            ])
        }
    
    def _generate_event_id(self, event_type: str, user_id: str, action: str) -> str:
        """生成事件ID"""
        data = f"{datetime.now().isoformat()}:{event_type}:{user_id}:{action}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """清理敏感参数"""
        sensitive_keys = ['password', 'token', 'secret', 'key', 'api_key']
        sanitized = {}
        
        for k, v in params.items():
            if any(sk in k.lower() for sk in sensitive_keys):
                sanitized[k] = "***REDACTED***"
            else:
                sanitized[k] = v
        
        return sanitized
    
    def _write_to_file(self, event: Dict[str, Any]):
        """写入日志文件"""
        with open(self.current_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')


class SecurityManager:
    """
    安全管理器
    
    整合权限管理和审计日志
    """
    
    def __init__(
        self,
        permission_manager: Optional[PermissionManager] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.permissions = permission_manager or PermissionManager()
        self.audit = audit_logger or AuditLogger()
        self._suspicious_patterns: List[str] = [
            "drop table", "delete from", "rm -rf",
            "__import__", "eval(", "exec("
        ]
    
    def check_and_log(
        self,
        user_id: str,
        permission: Permission,
        action_details: Dict[str, Any] = None
    ) -> bool:
        """检查权限并记录"""
        has_permission = self.permissions.check_permission(user_id, permission)
        
        self.audit.log(
            event_type="permission_check",
            user_id=user_id,
            action=f"check:{permission.value}",
            details=action_details,
            result="granted" if has_permission else "denied"
        )
        
        return has_permission
    
    def require_permission(
        self,
        user_id: str,
        permission: Permission
    ):
        """要求权限，否则抛出异常"""
        if not self.check_and_log(user_id, permission):
            self.audit.log_security_event(
                user_id=user_id,
                event="permission_denied",
                severity="warning",
                details={"permission": permission.value}
            )
            raise PermissionError(
                f"Permission denied: {permission.value}"
            )
    
    def scan_for_threats(self, content: str) -> List[Dict[str, Any]]:
        """扫描潜在威胁"""
        threats = []
        content_lower = content.lower()
        
        for pattern in self._suspicious_patterns:
            if pattern in content_lower:
                threats.append({
                    "pattern": pattern,
                    "severity": "high",
                    "position": content_lower.find(pattern)
                })
        
        return threats
    
    def sanitize_input(self, content: str) -> str:
        """清理用户输入"""
        # 基本的XSS防护
        content = content.replace("<script>", "")
        content = content.replace("</script>", "")
        
        return content
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """获取用户安全上下文"""
        policy = self.permissions.policies.get(user_id)
        if not policy:
            policy = self.permissions.create_default_policy(Role.USER)
        
        recent_events = self.audit.query(user_id=user_id, limit=10)
        
        return {
            "user_id": user_id,
            "role": policy.role.value,
            "permissions": [p.value for p in policy.allowed_permissions],
            "recent_activity": len(recent_events),
            "trust_score": self._calculate_trust_score(user_id, recent_events)
        }
    
    def _calculate_trust_score(
        self,
        user_id: str,
        recent_events: List[Dict[str, Any]]
    ) -> float:
        """计算用户信任分数"""
        if not recent_events:
            return 0.5
        
        # 基于历史行为计算
        denied_count = sum(
            1 for e in recent_events if e["result"] == "denied"
        )
        security_events = sum(
            1 for e in recent_events if e["event_type"] == "security"
        )
        
        score = 1.0 - (denied_count * 0.1) - (security_events * 0.2)
        return max(0.0, min(1.0, score))


# 使用示例
if __name__ == "__main__":
    # 创建安全管理器
    security = SecurityManager()
    
    # 设置用户权限
    admin_policy = AccessPolicy(
        role=Role.ADMIN,
        allowed_permissions=ROLE_PERMISSIONS[Role.ADMIN]
    )
    security.permissions.set_user_policy("user_001", admin_policy)
    
    user_policy = AccessPolicy(
        role=Role.USER,
        allowed_permissions=ROLE_PERMISSIONS[Role.USER],
        denied_tools={"system_shell", "file_delete"}
    )
    security.permissions.set_user_policy("user_002", user_policy)
    
    # 检查权限
    print("Admin can execute tools:",
          security.check_and_log("user_001", Permission.TOOL_EXECUTE))
    
    print("User can execute tools:",
          security.check_and_log("user_002", Permission.TOOL_EXECUTE))
    
    # 扫描威胁
    threats = security.scan_for_threats("Please eval(user_input) for processing")
    print("Threats found:", threats)
    
    # 生成审计报告
    report = security.audit.generate_report()
    print("\nAudit Report:", json.dumps(report, indent=2))
