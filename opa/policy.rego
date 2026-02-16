package istio.authz

import input.attributes.request.http as http_request

default allow = false

# 允许健康检查
allow {
    http_request.path == "/health"
}

# 允许已认证用户访问自己的资源
allow {
    some user_id
    jwt_payload.sub == user_id
    input.parsed_path[0] == "api"
    input.parsed_path[1] == "users"
    input.parsed_path[2] == user_id
}

# 管理员可以访问所有资源
allow {
    jwt_payload.realm_access.roles[_] == "admin"
}

# 提取 JWT payload
jwt_payload = payload {
    [_, payload, _] := io.jwt.decode(bearer_token)
}

bearer_token = t {
    v := http_request.headers.authorization
    startswith(v, "Bearer ")
    t := substring(v, count("Bearer "), -1)
}
