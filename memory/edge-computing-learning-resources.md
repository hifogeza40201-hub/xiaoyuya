# 边缘计算与IoT 学习资源推荐

## 一、官方文档与标准

### 通信协议标准
| 资源名称 | 链接 | 说明 |
|---------|------|------|
| MQTT v5.0 规范 | https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html | OASIS官方标准 |
| CoAP RFC 7252 | https://tools.ietf.org/html/rfc7252 | IETF官方RFC |
| OPC UA规范 | https://reference.opcfoundation.org/ | 工业互操作标准 |
| LoRaWAN规范 | https://lora-alliance.org/about-lorawan | LoRa联盟规范 |

### 云平台文档
| 资源名称 | 链接 | 说明 |
|---------|------|------|
| Azure IoT Docs | https://docs.microsoft.com/azure/iot-fundamentals/ | 微软IoT全家桶 |
| AWS IoT Core | https://docs.aws.amazon.com/iot/ | 亚马逊IoT服务 |
| 阿里云IoT | https://help.aliyun.com/product/30520.html | 国内首选 |
| 华为云IoTDA | https://support.huaweicloud.com/iothub/ | 华为IoT平台 |

### 开源项目
| 资源名称 | 链接 | 说明 |
|---------|------|------|
| EdgeX Foundry | https://edgexfoundry.org/ | LF Edge开源框架 |
| KubeEdge | https://kubeedge.io/ | K8s边缘扩展 |
| EMQX | https://www.emqx.io/ | 开源MQTT Broker |
| ThingsBoard | https://thingsboard.io/ | 开源IoT平台 |

---

## 二、在线课程

### 中文课程 (免费/付费)

| 平台 | 课程名 | 讲师/机构 | 适合人群 | 价格 |
|------|--------|-----------|---------|------|
| 慕课网 | 物联网开发入门到精通 | 官方 | 初学者 | ¥199 |
| 极客时间 | 从0开始搭建IoT平台 | 郭朝斌 | 后端开发者 | ¥99 |
| B站 | ESP32物联网开发实战 | 正点原子 | 硬件爱好者 | 免费 |
| B站 | 边缘计算技术与应用 | 阿里云 | 架构师 | 免费 |
| 网易云课堂 | 物联网系统设计 | 浙大 | 系统学习 | ¥299 |
| CSDN | MQTT协议深度解析 | 专家专栏 | 协议开发者 | ¥49 |

### 国际课程 (英文)

| 平台 | 课程名 | 机构 | 时长 | 证书 |
|------|--------|------|------|------|
| Coursera | IoT Programming and Big Data | UC San Diego | 4周 | 付费 |
| Coursera | Industrial IoT on Google Cloud | Google | 3周 | 付费 |
| edX | Introduction to the Internet of Things | Curtin University | 6周 | 免费旁听 |
| edX | Embedded Systems - Shape the World | UT Austin | 15周 | 付费 |
| Udemy | ESP32 + Arduino IoT Projects | Random Nerd | 12小时 | ¥100+ |
| Pluralsight | IoT Fundamentals | 多讲师 | 15小时 | 订阅制 |

---

## 三、推荐书籍

### 入门级
| 书名 | 作者 | 出版社 | ISBN |
|------|------|--------|------|
| 《物联网导论》 | 刘云浩 | 科学出版社 | 9787030416937 |
| 《图解物联网》 | [日] 宇佐美奈绪子 | 人民邮电 | 9787115451690 |
| 《MQTT权威指南》 | Gavin C. Copley | Packt | 9781787287815 |

### 进阶级
| 书名 | 作者 | 出版社 | ISBN | 重点 |
|------|------|--------|------|------|
| 《边缘计算：架构、技术与实践》 | 施巍松等 | 科学出版社 | 9787030630951 | 国内权威 |
| 《物联网架构设计》 | 付强 | 电子工业 | 9787121345678 | 架构思维 |
| 《嵌入式系统设计》 | 何立民 | 北航出版社 | 9787811242345 | 硬件基础 |

### 专业级
| 书名 | 作者 | 出版社 | ISBN | 重点 |
|------|------|--------|------|------|
| 《TinyML》 | Pete Warden | O'Reilly | 9781492047993 | 嵌入式AI |
| 《Embedded Systems Architecture》 | Tammy Noergaard | Newnes | 9780123821966 | 系统架构 |
| 《Real-Time Concepts for Embedded Systems》 | Qing Li | CMP | 9781578201242 | 实时系统 |

---

## 四、开发工具与平台

### 硬件开发板推荐

| 开发板 | 处理器 | 特点 | 价格 | 适用场景 |
|--------|--------|------|------|---------|
| **ESP32-DevKitC** | Xtensa LX6 | WiFi+BT、便宜、生态好 | ¥25 | IoT入门 |
| **树莓派4B** | BCM2711 | Linux完整、接口丰富 | ¥400 | 边缘网关 |
| **Jetson Nano** | ARM+GPU | AI推理、CUDA | ¥600 | 边缘AI |
| **STM32F407** | Cortex-M4 | 工业级、RTOS | ¥80 | 工控入门 |
| **Arduino Uno** | ATmega328P | 最简单、教程多 | ¥50 | 零基础 |

### 软件工具链

```
开发工具推荐:

IDE/编辑器:
├── PlatformIO (VS Code插件) - 跨平台开发神器 ⭐推荐
├── Arduino IDE - 入门首选
├── STM32CubeIDE - STM32官方IDE
├── Keil MDK - 传统ARM开发
└── Segger Embedded Studio - 免费商业级

仿真/调试:
├── Proteus - 电路仿真
├── QEMU - 系统仿真
├── J-Link - 调试器
└── ST-Link - STM32调试

协议测试:
├── MQTT.fx - MQTT客户端测试
├── Postman - HTTP/REST测试
├── Wireshark - 网络抓包
└── CoAP-cli - CoAP测试工具
```

### 云平台体验

| 平台 | 免费额度 | 特点 | 推荐度 |
|------|----------|------|--------|
| **ThingsBoard** | 开源免费 | 功能全、可私有部署 | ★★★★★ |
| **EMQX Cloud** | 1M连接分钟/月 | 专业MQTT | ★★★★★ |
| **阿里云IoT** | 100万条消息/月 | 国内服务稳定 | ★★★★☆ |
| **AWS IoT** | 125万条消息/月 | 全球服务 | ★★★★☆ |
| **巴法云** | 免费 | 国内轻量 | ★★★☆☆ |

---

## 五、社区与论坛

### 中文社区
| 社区 | 网址 | 特点 |
|------|------|------|
| 电子发烧友 | https://www.elecfans.com/ | 硬件资料全 |
| 21ic电子网 | https://www.21ic.com/ | 论坛活跃 |
| 开源中国IoT | https://www.oschina.net/iot | 开源项目 |
| 知乎IoT话题 | https://www.zhihu.com/topic/19591922 | 深度讨论 |
| CSDN IoT | https://iot.csdn.net/ | 技术博客 |

### 国际社区
| 社区 | 网址 | 特点 |
|------|------|------|
| Reddit r/IOT | https://www.reddit.com/r/IOT/ | 英文讨论 |
| Hackaday.io | https://hackaday.io/ | 创客项目 |
| Instructables | https://www.instructables.com/ | DIY教程 |
| Arduino Forum | https://forum.arduino.cc/ | 官方论坛 |
| ESP32 Forum | https://esp32.com/ | ESP32专属 |

---

## 六、实践项目推荐

### 入门项目 (1-2周)
1. **温湿度监测** - DHT22 + ESP32 + MQTT → 手机APP显示
2. **智能灯控** - LED + 光敏电阻 + WiFi → Web控制界面
3. **门窗报警** - 磁传感器 + 蜂鸣器 → 微信消息推送

### 进阶项目 (1个月)
1. **智能家居中控** - 多传感器 + Raspberry Pi + Node-RED
2. **AI门禁系统** - 摄像头 + Jetson Nano + 人脸识别
3. **小型气象站** - 多传感器 + LoRa → 数据上云

### 高级项目 (2-3个月)
1. **工业预测维护** - 振动传感器 + 边缘AI + 时序数据库
2. **无人零售结算** - 多摄像头 + 商品识别 + 边缘推理
3. **智慧农业系统** - 太阳能供电 + 自动灌溉 + 云端管理

---

## 七、认证考试

| 认证名称 | 颁发机构 | 难度 | 费用 | 有效期 |
|---------|---------|------|------|--------|
| AWS IoT Specialty | Amazon | ★★★★☆ | $300 | 3年 |
| Azure IoT Developer | Microsoft | ★★★☆☆ | $165 | 1年 |
| Google Cloud IoT | Google | ★★★☆☆ | $125 | 2年 |
| 阿里云物联网工程师 | 阿里云 | ★★★☆☆ | ¥600 | 2年 |
| 华为HCIA-IoT | 华为 | ★★☆☆☆ | ¥200 | 3年 |

---

## 八、学习路线图

```
IoT/边缘计算学习路径:

阶段1: 基础入门 (1-2个月)
├── 电子基础: 电路、传感器原理
├── C语言编程: 指针、结构体、内存管理
├── 单片机入门: Arduino/51 → STM32
└── 完成3个小项目

阶段2: 通信协议 (1个月)
├── 网络基础: TCP/IP、HTTP
├── MQTT协议: 发布订阅、QoS
├── 无线通信: WiFi、蓝牙、LoRa
└── 搭建MQTT Broker + 设备接入

阶段3: 边缘开发 (2个月)
├── Linux嵌入式: 交叉编译、驱动
├── RTOS: FreeRTOS任务调度
├── 边缘硬件: 树莓派/Jetson
└── 边缘AI: 模型部署与推理

阶段4: 云平台 (1个月)
├── 云原生基础: Docker、K8s
├── IoT平台: ThingsBoard/阿里云
├── 数据处理: 时序数据库、流处理
└── 完整项目: 设备→边缘→云端

阶段5: 进阶专题 (持续)
├── 边缘计算框架: KubeEdge/EdgeX
├── 安全: 加密、认证、安全启动
├── 性能优化: 低功耗、实时性
└── 行业解决方案

推荐学习顺序: 阶段1 → 阶段2 → 阶段3 → 阶段4 → 阶段5
```

---

## 九、推荐关注

### 技术博客/公众号
- 物联网智库
- RT-Thread物联网操作系统
- 边缘计算社区
- 阿里云IoT
- 华为IoT

### GitHub高星项目
| 项目 | Stars | 说明 |
|------|-------|------|
| home-assistant/core | 60k+ | 开源智能家居 |
| ThingsBoard | 14k+ | IoT平台 |
| emqx/emqx | 12k+ | MQTT Broker |
| kubeedge/kubeedge | 6k+ | 边缘K8s |
| espressif/arduino-esp32 | 11k+ | ESP32开发 |

---

*祝学习愉快！有任何问题欢迎交流讨论。*
