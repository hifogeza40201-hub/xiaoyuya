package istio.authz

test_allow_health_check {
    allow with input as {
        "attributes": {
            "request": {
                "http": {
                    "path": "/health",
                    "method": "GET"
                }
            }
        }
    }
}

test_deny_anonymous_admin_access {
    not allow with input as {
        "attributes": {
            "request": {
                "http": {
                    "path": "/api/admin/users",
                    "method": "GET",
                    "headers": {}
                }
            }
        }
    }
}

# 运行测试: opa test -v .
