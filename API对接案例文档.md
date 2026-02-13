# REST API 对接案例文档

> 文档生成时间：2026-02-13  
> 学习目标：掌握REST API基础、HTTP方法、JSON格式及实际调用

---

## 一、REST API 基础概念

### 1.1 什么是 REST API

**REST**（Representational State Transfer，表现层状态转换）是一种软件架构风格，用于设计网络应用程序的通信方式。

**API**（Application Programming Interface，应用程序编程接口）是软件系统之间交互的接口。

**REST API** 是基于HTTP协议的API设计风格，具有以下特点：

| 特点 | 说明 |
|------|------|
| 无状态 | 每个请求独立，服务器不保存客户端状态 |
| 统一接口 | 使用标准的HTTP方法进行操作 |
| 资源导向 | 一切皆资源，通过URL标识 |
| 可缓存 | 响应可以被客户端或中间层缓存 |

### 1.2 REST API 基本结构

```
https://api.example.com/v1/users/123
\____/   \_____________/ \|/ \___/ \__/
  |            |           |    |    |
协议        域名/主机     版本 资源  资源ID
```

---

## 二、HTTP 方法详解

HTTP方法是REST API的核心，定义了对资源的操作类型：

| HTTP方法 | 操作 | 描述 | 幂等性 |
|----------|------|------|--------|
| **GET** | 读取 | 获取资源信息 | ✓ 幂等 |
| **POST** | 创建 | 创建新资源 | ✗ 非幂等 |
| **PUT** | 更新 | 完全替换资源 | ✓ 幂等 |
| **PATCH** | 部分更新 | 修改资源的部分字段 | ✗ 非幂等 |
| **DELETE** | 删除 | 删除指定资源 | ✓ 幂等 |

> **幂等性**：多次执行相同操作，结果一致

### 2.1 GET 请求示例
```powershell
# 获取单个用户信息
Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/users/1"

# 获取所有文章列表
Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/posts"
```

### 2.2 POST 请求示例
```powershell
$body = @{
    title = '新文章标题'
    body = '文章内容'
    userId = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/posts" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

---

## 三、JSON 数据格式

**JSON**（JavaScript Object Notation）是REST API最常用的数据交换格式。

### 3.1 JSON 基本语法

```json
{
    "name": "张三",
    "age": 25,
    "isStudent": false,
    "scores": [85, 90, 78],
    "address": {
        "city": "北京",
        "zipCode": "100000"
    }
}
```

### 3.2 JSON 数据类型

| 类型 | 示例 | PowerShell对应 |
|------|------|----------------|
| 字符串 | `"hello"` | System.String |
| 数字 | `25`, `3.14` | System.Int32 / Double |
| 布尔 | `true`, `false` | System.Boolean |
| 数组 | `[1, 2, 3]` | System.Array |
| 对象 | `{"a": 1}` | PSCustomObject |
| null | `null` | $null |

### 3.3 PowerShell 与 JSON 转换

```powershell
# PowerShell对象转JSON
$object = @{ name = "测试"; value = 123 }
$json = $object | ConvertTo-Json

# JSON转PowerShell对象
$parsed = $json | ConvertFrom-Json
```

---

## 四、实际案例：天气API集成

### 4.1 选用 API

**Open-Meteo** - 免费开源的天气API
- 官网：https://open-meteo.com/
- 特点：无需API密钥，支持全球天气数据
- 数据类型：温度、风速、降水、湿度等

### 4.2 获取北京天气数据

#### API端点
```
https://api.open-meteo.com/v1/forecast
```

#### 请求参数

| 参数 | 值 | 说明 |
|------|-----|------|
| latitude | 39.9042 | 纬度（北京） |
| longitude | 116.4074 | 经度（北京） |
| current_weather | true | 获取当前天气 |
| timezone | Asia/Shanghai | 时区 |

#### PowerShell 调用代码

```powershell
# 构建API URL
$apiUrl = "https://api.open-meteo.com/v1/forecast" +
          "?latitude=39.9042" +
          "&longitude=116.4074" +
          "&current_weather=true" +
          "&timezone=Asia/Shanghai"

# 发送GET请求
$response = Invoke-RestMethod -Uri $apiUrl

# 输出原始JSON
$response | ConvertTo-Json -Depth 10

# 提取关键信息
Write-Host "=== 北京当前天气 ===" -ForegroundColor Green
Write-Host "温度: $($response.current_weather.temperature)°C"
Write-Host "风速: $($response.current_weather.windspeed) km/h"
Write-Host "风向: $($response.current_weather.winddirection)°"
Write-Host "时间: $($response.current_weather.time)"
```

#### 实际响应数据

```json
{
    "latitude": 39.875,
    "longitude": 116.375,
    "generationtime_ms": 0.057578086853027344,
    "utc_offset_seconds": 28800,
    "timezone": "Asia/Shanghai",
    "timezone_abbreviation": "GMT+8",
    "elevation": 47.0,
    "current_weather_units": {
        "time": "iso8601",
        "interval": "seconds",
        "temperature": "°C",
        "windspeed": "km/h",
        "winddirection": "°",
        "is_day": "",
        "weathercode": "wmo code"
    },
    "current_weather": {
        "time": "2026-02-13T09:45",
        "interval": 900,
        "temperature": 3.8,
        "windspeed": 0.8,
        "winddirection": 333,
        "is_day": 1,
        "weathercode": 0
    }
}
```

#### 数据解析

| 字段 | 值 | 含义 |
|------|-----|------|
| temperature | 3.8°C | 当前温度 |
| windspeed | 0.8 km/h | 风速 |
| winddirection | 333° | 风向（北偏西）|
| is_day | 1 | 白天(1) / 夜间(0) |
| weathercode | 0 | 天气代码（0=晴朗）|
| time | 2026-02-13T09:45 | 数据时间 |

---

## 五、实际案例：用户管理API

### 5.1 选用 API

**JSONPlaceholder** - 免费的测试用REST API
- 官网：https://jsonplaceholder.typicode.com/
- 特点：模拟真实CRUD操作，支持GET/POST/PUT/DELETE

### 5.2 GET 请求 - 获取用户信息

```powershell
# 获取ID为1的用户信息
$user = Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/users/1"

# 输出结果
$user | Select-Object id, name, email, phone | ConvertTo-Json
```

**响应结果：**
```json
{
    "id": 1,
    "name": "Leanne Graham",
    "email": "Sincere@april.biz",
    "phone": "1-770-736-8031 x56442"
}
```

### 5.3 POST 请求 - 创建新文章

```powershell
# 构建请求体（PowerShell对象）
$newPost = @{
    title = 'API测试文章'
    body = '这是通过PowerShell创建的测试内容'
    userId = 1
}

# 转换为JSON格式
$jsonBody = $newPost | ConvertTo-Json

# 发送POST请求
$createdPost = Invoke-RestMethod `
    -Uri "https://jsonplaceholder.typicode.com/posts" `
    -Method POST `
    -ContentType "application/json" `
    -Body $jsonBody

# 输出创建的帖子
$createdPost | ConvertTo-Json
```

**响应结果：**
```json
{
    "title": "API测试文章",
    "body": "这是通过PowerShell创建的测试内容",
    "userId": 1,
    "id": 101
}
```

> 注意：JSONPlaceholder是测试API，POST请求不会真正创建数据，但会返回模拟的响应（id=101）

---

## 六、完整PowerShell脚本

```powershell
<#
.SYNOPSIS
    REST API 集成示例脚本
.DESCRIPTION
    演示如何使用PowerShell调用REST API
    包含天气API和用户管理API的调用示例
#>

# 设置输出编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Get-WeatherInfo {
    param(
        [double]$Latitude = 39.9042,   # 默认北京纬度
        [double]$Longitude = 116.4074   # 默认北京经度
    )
    
    Write-Host "=== 获取天气信息 ===" -ForegroundColor Cyan
    
    $apiUrl = "https://api.open-meteo.com/v1/forecast" +
              "?latitude=$Latitude" +
              "&longitude=$Longitude" +
              "&current_weather=true" +
              "&timezone=Asia/Shanghai"
    
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop
        
        [PSCustomObject]@{
            城市 = "坐标: $Latitude, $Longitude"
            温度 = "$($response.current_weather.temperature)°C"
            风速 = "$($response.current_weather.windspeed) km/h"
            风向 = "$($response.current_weather.winddirection)°"
            时间 = $response.current_weather.time
        }
    }
    catch {
        Write-Error "获取天气信息失败: $_"
    }
}

function Get-UserInfo {
    param([int]$UserId = 1)
    
    Write-Host "=== 获取用户信息 ===" -ForegroundColor Cyan
    
    try {
        $user = Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/users/$UserId"
        
        [PSCustomObject]@{
            ID = $user.id
            姓名 = $user.name
            邮箱 = $user.email
            电话 = $user.phone
            网站 = $user.website
        }
    }
    catch {
        Write-Error "获取用户信息失败: $_"
    }
}

function New-BlogPost {
    param(
        [string]$Title = "默认标题",
        [string]$Body = "默认内容",
        [int]$UserId = 1
    )
    
    Write-Host "=== 创建新文章 ===" -ForegroundColor Cyan
    
    $postData = @{
        title = $Title
        body = $Body
        userId = $UserId
    } | ConvertTo-Json
    
    try {
        $result = Invoke-RestMethod `
            -Uri "https://jsonplaceholder.typicode.com/posts" `
            -Method POST `
            -ContentType "application/json" `
            -Body $postData
        
        Write-Host "文章创建成功! 分配ID: $($result.id)" -ForegroundColor Green
        $result
    }
    catch {
        Write-Error "创建文章失败: $_"
    }
}

# ========== 执行示例 ==========

# 1. 获取北京天气
Get-WeatherInfo

# 2. 获取用户信息
Get-UserInfo -UserId 1

# 3. 创建新文章
New-BlogPost -Title "PowerShell API测试" -Body "这是一篇测试文章"
```

---

## 七、常见HTTP状态码

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权（需认证）|
| 403 | Forbidden | 禁止访问 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务不可用 |

---

## 八、API 调试技巧

### 8.1 使用 -Verbose 参数查看详细请求信息
```powershell
Invoke-RestMethod -Uri $url -Verbose
```

### 8.2 处理API错误
```powershell
try {
    $response = Invoke-RestMethod -Uri $url -ErrorAction Stop
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "请求失败，状态码: $statusCode" -ForegroundColor Red
}
```

### 8.3 添加请求头
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Accept" = "application/json"
}

Invoke-RestMethod -Uri $url -Headers $headers
```

---

## 九、总结

通过本次学习，我们掌握了：

1. ✅ **REST API 基础概念** - 理解资源导向的API设计
2. ✅ **HTTP 方法** - GET/POST/PUT/DELETE 的使用场景
3. ✅ **JSON 格式** - 数据序列化与反序列化
4. ✅ **API 调用实战** - 使用 PowerShell Invoke-RestMethod
5. ✅ **错误处理** - 异常捕获与状态码处理

### 下一步学习建议

- 学习API认证方式（API Key、OAuth2、JWT）
- 了解分页、限流等高级API特性
- 学习使用Postman进行API测试
- 探索GraphQL等新型API查询语言

## 十、实际运行结果

以下是执行 `API_Demo.ps1` 脚本的实际输出：

```
========================================
     REST API Integration Demo
========================================

=== Weather Info [Beijing] ===
URL: https://api.open-meteo.com/v1/forecast?latitude=39.9042&longitude=116.4074...

Weather Report:
  City: Beijing
  Condition: Clear sky
  Temperature: 3.8 C
  Wind Speed: 0.8 km/h
  Wind Direction: 333 degrees
  Time: 2026-02-13T09:45

=== User Info [ID: 1] ===

User Details:
  ID: 1
  Name: Leanne Graham
  Username: Bret
  Email: Sincere@april.biz
  Phone: 1-770-736-8031 x56442
  Website: hildegard.org
  Company: Romaguera-Crona
  City: Gwenborough

=== Create New Post ===
Request Body: {
    "title": "PowerShell REST API Tutorial",
    "body": "Today I learned how to call REST APIs...",
    "userId": 1
}

[SUCCESS] Post Created!
  Post ID: 101
  Title: PowerShell REST API Tutorial
  User ID: 1

========================================
         Demo Completed!
========================================
```

---

*文档生成时间：2026-02-13*
