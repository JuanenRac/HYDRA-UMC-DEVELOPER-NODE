<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - Developer node: evidence, repro cases and checkouts, approved by a person
Copyright (C) JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

<p align="center">
  <img src="images/HYDRA_UMC_BANNER.svg" alt="HYDRA-UMC-DEVELOPER-NODE banner" width="100%">
</p>

# 🧑‍💻 HYDRA-UMC-DEVELOPER-NODE

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | 🇨🇳 <b>简体中文</b> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 🧑‍💻 开发节点：研究并复现故障，未经批准不运行任何内容

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0--or--later-blue.svg" alt="GPL 3.0 or later">
  <img src="https://img.shields.io/badge/Language-Python%203.11%2B-blue.svg" alt="Language">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="Core">
  <img src="https://img.shields.io/badge/Parts-closed%20by%20default-367BF5.svg" alt="Parts">
  <img src="https://img.shields.io/badge/Tests-70%20passing-2ea44f.svg" alt="Tests">
  <img src="https://img.shields.io/badge/Version-0.0.2-0f6cbd.svg" alt="Version">
  <img src="https://img.shields.io/badge/Maturity-scaffolding-FFB020.svg" alt="Maturity">
</p>

---

**诚实检查 - 目前实际能运行的内容：** 证据接收（签名、nonce、校验和、机密检查）、批准与摘要绑定的可执行复现案例、带上限的检出缓存、状态文档、`ecosystem-ci` 插件以及八种语言的文本都是真实且经过测试的（70 个自动测试，使用本地 git 仓库和本地进程）。该节点尚未在真实开发主机上运行，配方除白名单和最小环境外没有其他隔离，也没有任何东西会自行从队列取活。已交付的确切内容见 `CHANGELOG.md`。

---

> **安全与安防现状:**本生态系统不是经认证的安全系统。目前尚无硬件 E-STOP 通路,没有由固件强制执行的限位或联锁,也没有经过验证的运动指令;固件映像使用 CRC-32 和 Ed25519 签名校验,发布构建会拒绝已公开的开发密钥(中继之后的工具头和扩展板仍运行 URTC 的引导程序,它们使用共享密钥的 HMAC-SHA256 而不是签名);TLS 与双向 TLS 均为可选项,默认关闭;自制电路板尚未组装或测试。在依赖此处任何说法来保障人身安全之前,请先阅读[安全基线](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md)和[威胁模型](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md)。

---

## 📋 速览

| | |
|---|---|
| 版本 | `0.0.2` |
| 成熟度 | 雏形 |
| 测试 | 70 (`python -m pytest -q tests`) |
| 技术栈 | Python 3.11+ / JSON Schema / SQLite / git worktree |
| 目标 | 开发服务器 |
| 真实硬件 | 不适用：这里的内容不在硬件上运行 |

**跳转：** [概述](#-概述) · [架构](#-架构) · [快速开始](#-快速开始) · [测试](#-测试) · [仓库结构](#-仓库结构) · [相关项目](#-相关项目)

## 🚦 项目状态

每一行是本仓库的一个部分，灯号表示它今天做到了哪一步。内容依据仓库能够展示的证据（测试、构建、运行），而不是计划。

🟢 已完成并验证 · 🟡 可用，有已知限制 · 🟠 部分完成或尚未验证 · 🔴 未完成或不可用

| 领域 | 状态 | 在这里的含义 |
|---|---|---|
| 软件 | 🟠 | 目前只有结构和最初的部分，大部分工作尚未完成 |
| 测试 | 🟡 | 70 项自动测试，每次变更都会运行 |
| 真实硬件 | 🟡 | 不适用：这里的内容不在硬件上运行 |
| 接口与协议 | 🟡 | 提供的路由或消息已有文档，并用客户端测试过；尚未被所有客户端使用 |
| 集成 | 🟡 | 其消息和路由已对照 SDK 的共享契约检查；尚未与真实设备一起运行 |
| 安全性 | 🟡 | 访问控制、输入限制或签名已实现并在计算机上测试；项目之外无人审查过 |
| 运维 | 🟠 | 会写日志；尚无指标或健康检查端点 |
| 文档 | 🟡 | 八种语言的 README，每次变更都会与清单核对 |

## 🎯 概述

HYDRA-UMC-DEVELOPER-NODE 是生态系统的开发节点：研究某个节点所报告故障的地方。它以只读方式读取 `HYDRA-UMC-LOCAL-TECHNICIAN` 的证据包，从 git worktree 缓存中获取相关修订的确切源码，用固定配方复现故障，并可在工作区上运行共享 CI。

有四条规则处处成立。每个部分在配置文件打开之前都是**关闭**的。没有**人工批准将要运行的确切内容**，任何东西都不会运行。任何内容都**不会离开这台机器**。所有可调的值都在**配置文件**里，绝不写进代码。

此版本包含五个相互独立的部分：

1. **证据接收**（`evidence.py`）- 校验证据包或已签名的 `incident-transport/1` 消息（签名、接收方、时效、nonce、格式、校验和、无机密），并保存为等待人工处理的案例。
2. **可执行的复现案例**（`repro.py`、`approvals.py`）- 由参数列表组成的配方，只允许列出的命令，批准与其摘要绑定；每次运行都是 SDK 的 `ScenarioOutcome`，修复前后一对结果的结论由 SDK 给出。
3. **按修订版本的检出缓存**（`checkouts.py`）- 一个 bare 镜像加每个提交一个 git worktree，固定的提交会被验证，通过删除最久未使用的 worktree 来保持 GB 上限。
4. **状态文档**（`panel.py`）- 为仪表板或工作室提供队列、日志和健康状况，支持八种语言，以文件形式提供。
5. **`ecosystem-ci` 插件**（`plugin_ci.py`）- 运行工作区中每个仓库的共享 CI 校验，并生成一份汇总报告。在完整模式（默认关闭）下，它还可以运行每个仓库声明的重型测试：由人工按摘要批准的一个批次，一次一个仓库，并对时间、输出和剩余磁盘空间设限。

## 🧩 在 HYDRA-UMC 中的角色

**HYDRA-UMC-DEVELOPER-NODE** 是生态系统的开发节点：它读取 `HYDRA-UMC-LOCAL-TECHNICIAN` 的证据包，维护按修订版本的检出缓存，运行复现配方和共享 CI；这些部分在配置将其打开、且有人批准确切的运行之前都保持关闭。

## 🏛️ 架构

<p align="center">
  <img src="images/architecture.svg" alt="HYDRA-UMC-DEVELOPER-NODE architecture" width="100%">
</p>

## 🚀 快速开始

需要 Python 3.11 或更高版本。

```bash
./build.sh  # Linux, macOS (build.bat on Windows)
./run.sh
./run.sh --config configs/developer-node.json evidence verify bundle.json
```

## 🧪 测试

运行 `python -m pytest -q tests` 会执行 70 个自动测试。 不需要硬件，也不需要这台机器以外的任何东西。

CI 运行 `HYDRA_UMC_CI=1 python tools/ci_validate.py`，检查清单、文档、八个 README 和图片。

## 🏗️ 构建与发布

```bash
chmod +x build.sh   # 仅需一次
./build.sh          # 创建 .venv，pip install -e ".[dev]"，检查编译并运行测试
./run.sh            # 检查随附的配置（所有开关均关闭）
./run.sh --config configs/developer-node.json evidence verify bundle.json
./run.sh --version
```

在 Windows 上：先 `build.bat`，再 `run.bat`。`test.sh` / `test.bat` 运行测试和检查，不改变版本。修复前后一对结果的结论需要 SDK：`pip install -e ".[dev,sdk]"`。

**故障排查**

- `已拒绝：... is closed`：该部分处于关闭状态。请在配置文件中打开它（`"enabled": true`，必须是真正的布尔值），并阅读 [docs/CONFIGURATION.md](docs/CONFIGURATION.md)。
- `no valid approval for this exact recipe`：用 `repro approve` 重新批准该配方；批准会过期，且只能使用一次。
- `an approval needs a person at a terminal`：请在终端中进行批准，而不是通过脚本或管道。

## 📂 仓库结构

<p align="center">
  <img src="images/repository-structure.svg" alt="Repository structure of HYDRA-UMC-DEVELOPER-NODE" width="100%">
</p>

<details>
<summary>目录树的文本版本</summary>

```text
HYDRA-UMC-DEVELOPER-NODE/
├── src/hydra_umc_developer_node/   源代码
│   ├── cli.py                      命令行
│   ├── settings.py                 配置与开关
│   ├── evidence.py                 证据包的校验与接收
│   ├── repro.py                    复现配方与运行
│   ├── checkouts.py                按修订版本的检出缓存
│   ├── panel.py                    面向仪表板的状态文档
│   ├── plugin_ci.py                ecosystem-ci 插件
│   ├── plugin_full.py              ecosystem-ci 插件的完整模式
│   ├── approvals.py                由人工批准
│   ├── store.py                    本地数据库与日志
│   ├── schema.py                   合约校验
│   ├── redaction.py                机密脱敏
│   └── i18n.py                     八种语言的文本
├── contracts/                      JSON Schema 合约
├── tests/                          自动测试
├── configs/                        示例配置，全部关闭
├── docs/                           项目文档
├── tools/                          项目工具和 CI 检查
├── images/                         媒体资源与应用图标
├── .github/                        CI 工作流和 Issue 模板
├── build.sh / build.bat            虚拟环境 + 可编辑安装 + 编译检查 + 测试
├── run.sh / run.bat                转发一条真实的 CLI 命令
├── bump_version.py                 显式提升版本
├── bump_manifest_version.py        将 hydra-umc.project.json 的版本与原生版本同步（--sync）
├── CHANGELOG.md                    每个版本的变更
├── build-test.sh                   不修改内容的构建检查
├── hydra-umc.project.json          清单：版本、成熟度、系列
├── pyproject.toml                  包的元数据
└── test.sh                         运行测试
```

</details>

## 🗺️ 路线图与已知限制

**当前已知限制**

此版本包含上述五个部分。尚未具备的内容：

- **运行的隔离。** 配方以运行节点的用户权限执行，带有程序白名单、最小环境以及时间和输出限制；周围还没有沙箱（容器、命名空间）。批准之前必须有人阅读配方。
- **更强的批准。** 批准是在终端中写入本地数据库的一条记录，并未用批准者的密钥签名。
- **另一侧的面板。** 状态文档是一份契约和一个文件；`HYDRA-UMC-DASHBOARD-AI` 和 `HYDRA-UMC-STUDIO` 目前还不显示它，文件如何送达（经过认证的隧道）由它们自行决定。
- **工作循环。** 案例、配方和检出通过命令使用；没有任何东西会自行从队列取出案例去处理，这是有意为之。
- **在真实开发主机上运行。** 该节点仅在带有本地 git 仓库的计算机上测试过。

## 🌍 语言

本 README 和仓库文档提供八种语言：英语、西班牙语、德语、法语、意大利语、日语、中文和葡萄牙语（葡萄牙）。它们同时编写，并由 CI 检查八个文件拥有相同的章节和相同的链接。 本仓库没有自己的界面或消息目录，因此没有需要翻译的界面文字。

## 🔗 相关项目

本项目是同一作者(JuanenRac / Electro Hobby 3D)打造的 HYDRA-UMC 机器人生态系统的一部分。值得了解,因为某个请求实际上可能是关于这些项目之一,而非本仓库本身。

**直接相关**
- **[HYDRA-UMC-LOCAL-TECHNICIAN](https://github.com/JuanenRac/HYDRA-UMC-LOCAL-TECHNICIAN)** — 生成本节点读取的证据包；节点只负责校验和保存，绝不修改它们，也不执行其中所写的内容。
- **[HYDRA-UMC-DEV-SERVER](https://github.com/JuanenRac/HYDRA-UMC-DEV-SERVER)** — 具有持久任务队列的可复现开发主机；本节点是更轻量的地方，在人工批准每次运行后研究并复现故障。
- **[HYDRA-UMC-OPS-AGENT](https://github.com/JuanenRac/HYDRA-UMC-OPS-AGENT)** — 负责维护事件的生命周期（证据、诊断、经人工批准的变更、金丝雀部署、验证）；本节点提供复现步骤，绝不批准变更。
- **[HYDRA-UMC-SDK](https://github.com/JuanenRac/HYDRA-UMC-SDK)** — 共享契约：每次复现运行的场景结果遵循其模式，修复前后一对结果的结论由 SDK 计算。

**生态系统中的其他项目**

*核心硬件与平台*
- **[HYDRA-UMC](https://github.com/JuanenRac/HYDRA-UMC)** — 机器人手臂主板设计——CM5 主机 + 双核 STM32H745,目标是通过 CAN-OTA/SPI-OTA 协调最多 8 条工具臂(固件处于早期阶段,尚无已组装的电路板)。
- **[HYDRA-UMC-OS](https://github.com/JuanenRac/HYDRA-UMC-OS)** — 面向 CM5 的可复现 Raspberry Pi OS 产品层——只读代理、经过验证的配置/配置文件、WiFi 首次配网。

*核心后端与客户端*
- **[HYDRA-UMC-SERVER](https://github.com/JuanenRac/HYDRA-UMC-SERVER)** — 每个控制客户端真正通信的真实无头后端(REST/WebSocket)。
- **[HYDRA-UMC-STUDIO](https://github.com/JuanenRac/HYDRA-UMC-STUDIO)** — 具有实时多机器人 3D 可视化的网页控制面板。
- **[HYDRA-UMC-SUITE](https://github.com/JuanenRac/HYDRA-UMC-SUITE)** — 面向多台服务器的桌面(PySide6)集群指挥中心。
- **[HYDRA-UMC-ANDROID-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-ANDROID-CONTROL)** — 具有生物识别登录和配对 Wear OS 伴侣应用的原生 Android 控制应用。
- **[HYDRA-UMC-IOS-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-IOS-CONTROL)** — 具有实时 WebSocket 同步的 iOS/iPadOS 控制应用(Flutter)。
- **[HYDRA-UMC-DSI](https://github.com/JuanenRac/HYDRA-UMC-DSI)** — 面向机载 7 英寸 DSI 触摸屏的原生触控界面，直接嵌入 CM5 本体。
- **[HYDRA-UMC-EDITOR-URDF](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-URDF)** — 将完成的模型推送到 STUDIO 自身目录的桌面版图形化 URDF 创建/编辑工具。
- **[HYDRA-UMC-EDITOR-STL](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-STL)** — 桌面 STL 模型编辑器，在 HYDRA-UMC-EDITOR-URDF 编辑的同一模型目录中变换/替换/移除/添加真实部件。
- **[HYDRA-UMC-BRIDGE-AMR](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-AMR)** — 通过 VDA 5050 MQTT 发布者为 AGV/AMR 车队提供的协调边界(仅针对仿真车队测试)。
- **[HYDRA-UMC-BRIDGE-CNC](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-CNC)** — 具备 GRBL 状态/控制字节访问能力的高层 CNC 单元协调器(仅针对模拟器测试)。
- **[HYDRA-UMC-BRIDGE-DROIDS](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-DROIDS)** — 面向足式/人形机器人的协调边界,带有 Boston Dynamics Spot 指令发送器(仅针对模拟器测试)。
- **[HYDRA-UMC-BRIDGE-LASER](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-LASER)** — 读取 3 路钥匙/外壳/联锁 GPIO 信号的激光单元协调器(仅针对模拟芯片测试;无法使激光器上膛或发射)。
- **[HYDRA-UMC-BRIDGE-OPENPNP](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-OPENPNP)** — 面向 OpenPnP 贴片机板级流程的安全高层协调器。
- **[HYDRA-UMC-BRIDGE-PRINTER3D](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-PRINTER3D)** — 面向 Moonraker/Klipper 3D 打印机的安全协调边界，具备真实的受控作业指令。
- **[HYDRA-UMC-BRIDGE-ROS2](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-ROS2)** — 带有惰性导入 rclpy ROS 2 传输层的协调器(尚未在 ROS 2 环境中运行)。
- **[HYDRA-UMC-BRIDGE-UAV](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-UAV)** — 面向搭载摄像头的无人机的协调边界,带有 MAVLink 指令发送器(仅针对模拟器测试)。

*URTC 工具平台*
- **[URTC](https://github.com/JuanenRac/URTC)** — 面向实体 Universal Robot Tool Controller 板卡的固件，通过 CAN 总线支持 25 种以上工具配置。
- **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** — 面向 URTC 板卡的桌面图形烧录工具，支持 CAN-OTA 以及全芯片 SWD/JTAG。
- **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** — 面向 URTC 板卡的桌面实时 CAN 总线诊断工具，每种工具配置对应一个面板。
- **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** — 通过 Web Serial API 实现的浏览器版 URTC-TESTER 替代方案，无需本地安装。
- **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** — URTC CAN 总线前的网关：允许的标识符列表、速率限制和会话密钥；软件已在计算机上测试，尚未在真实总线上测试。

*视觉 AI 节点(Hailo-8)*
- **[HYDRA-UMC-VISION-NODE](https://github.com/JuanenRac/HYDRA-UMC-VISION-NODE)** — 面向 Hailo-8 视觉流水线的集成中枢，具备逐阶段的真实硬件就绪检测。
- **[HYDRA-UMC-DETECTION-HEF](https://github.com/JuanenRac/HYDRA-UMC-DETECTION-HEF)** — 具备 Hailo 架构/校验和安全加载验证的真实编译模型注册表。
- **[HYDRA-UMC-VISION-STREAMER](https://github.com/JuanenRac/HYDRA-UMC-VISION-STREAMER)** — 具备真实 HailoRT 集成边界的真实 GStreamer 流水线 + MediaMTX 配置生成器。
- **[HYDRA-UMC-VISUAL-SERVOING-API](https://github.com/JuanenRac/HYDRA-UMC-VISUAL-SERVOING-API)** — 以区域状态为授权条件的 Position-Based Visual Servoing 修正律;尚无摄像头位姿估计。
- **[HYDRA-UMC-SAFETY-ZONES](https://github.com/JuanenRac/HYDRA-UMC-SAFETY-ZONES)** — 从文件读取物体位置的 v0 区域入侵、校准新鲜度与 E-STOP 请求逻辑;没有检测器为其供数,也尚未连接任何物理 E-STOP。

*认知 AI 节点(Hailo-10)*
- **[HYDRA-UMC-COGNITIVE-NODE](https://github.com/JuanenRac/HYDRA-UMC-COGNITIVE-NODE)** — 面向 Hailo-10 认知流水线(LLM/VLA/语音编排)的集成中枢。
- **[HYDRA-UMC-VLA-ENGINE](https://github.com/JuanenRac/HYDRA-UMC-VLA-ENGINE)** — 面向 Vision-Language-Action 模型的真实动作 token 编解码与轨迹生成。
- **[HYDRA-UMC-VOICE-UI](https://github.com/JuanenRac/HYDRA-UMC-VOICE-UI)** — 具备受限、需确认的 Watch 中继的真实语音前端(VAD + 意图解析)——它没有出站通知接口，因此本项目改为把事件发布到生态系统的代理（broker）。
- **[HYDRA-UMC-SEMANTIC-PLANNER](https://github.com/JuanenRac/HYDRA-UMC-SEMANTIC-PLANNER)** — 基于真实规则的任务分解，以及针对 MCU 错误码的语义化错误恢复。
- **[HYDRA-UMC-DOCS-QA](https://github.com/JuanenRac/HYDRA-UMC-DOCS-QA)** — 面向本生态系统自身 Markdown 文档的真实纯标准库 TF-IDF 文档检索。

*编排与集群*
- **[HYDRA-UMC-ORCHESTRATOR](https://github.com/JuanenRac/HYDRA-UMC-ORCHESTRATOR)** — 具备真实 gRPC/Protobuf 健康报告契约与任务状态机的集成中枢。
- **[HYDRA-UMC-JOB-DISPATCHER](https://github.com/JuanenRac/HYDRA-UMC-JOB-DISPATCHER)** — 基于真实 HTTP API 的真实优先级任务队列，支持去重。
- **[HYDRA-UMC-PATH-PLANNER-3D](https://github.com/JuanenRac/HYDRA-UMC-PATH-PLANNER-3D)** — 具备真实障碍物/工作空间碰撞校验的真实基于 RRT 的三维路径规划器。
- **[HYDRA-UMC-SWARM-SYNC](https://github.com/JuanenRac/HYDRA-UMC-SWARM-SYNC)** — 经过多单元收敛属性测试的真实 CRDT LWW-Element-Map 状态同步。
- **[HYDRA-UMC-NODE-HEALING](https://github.com/JuanenRac/HYDRA-UMC-NODE-HEALING)** — 基于 gRPC 的真实车队健康看门狗，具备自身的重试/退避机制及身份不匹配检测。

*数字孪生与仿真*
- **[HYDRA-UMC-TWIN](https://github.com/JuanenRac/HYDRA-UMC-TWIN)** — 面向数字孪生引擎的集成中枢，具备真实的版本兼容性同步契约。
- **[HYDRA-UMC-HIL-BRIDGE](https://github.com/JuanenRac/HYDRA-UMC-HIL-BRIDGE)** — 在仿真与真实硬件之间带有软件碰撞联锁的硬件在环路由器(未在真实硬件上测试)。
- **[HYDRA-UMC-PHYSICS-REPLICA](https://github.com/JuanenRac/HYDRA-UMC-PHYSICS-REPLICA)** — 面向真实 URDF 子集的真实正向运动学与关节限位校验。
- **[HYDRA-UMC-SYNTHETIC-DATA-GEN](https://github.com/JuanenRac/HYDRA-UMC-SYNTHETIC-DATA-GEN)** — 具备 YOLO/COCO 标注导出功能的真实程序化 2D 场景生成器。

*数据与分析*
- **[HYDRA-UMC-DATALAKE](https://github.com/JuanenRac/HYDRA-UMC-DATALAKE)** — 具备真实数据摄入/查询 HTTP API 的真实 sqlite3 时序数据存储。
- **[HYDRA-UMC-ANOMALY-DETECTOR](https://github.com/JuanenRac/HYDRA-UMC-ANOMALY-DETECTOR)** — 具备漂移监测能力的真实 FFT + 统计基线异常检测器。
- **[HYDRA-UMC-PRODUCTION-REPORTS](https://github.com/JuanenRac/HYDRA-UMC-PRODUCTION-REPORTS)** — 基于 DATALAKE 历史数据的真实 OEE/可用率计算，支持可复现的 CSV 导出。
- **[HYDRA-UMC-TELEMETRY-COLLECTOR](https://github.com/JuanenRac/HYDRA-UMC-TELEMETRY-COLLECTOR)** — 面向 DATALAKE 的真实 CAN/WebSocket 数据摄入管道，支持序列去重。

*工业网关*
- **[HYDRA-UMC-GATEWAY-INDUSTRIAL](https://github.com/JuanenRac/HYDRA-UMC-GATEWAY-INDUSTRIAL)** — 中继至工业协议的集成中枢，具备真实的指令白名单/背压控制层。
- **[HYDRA-UMC-OPCUA-SERVER](https://github.com/JuanenRac/HYDRA-UMC-OPCUA-SERVER)** — 经真实二进制协议客户端会话验证的真实 OPC-UA 地址空间。
- **[HYDRA-UMC-MQTT-BROKER](https://github.com/JuanenRac/HYDRA-UMC-MQTT-BROKER)** — 具备可选按客户端认证与主题 ACL 的真实 MQTT 代理。
- **[HYDRA-UMC-MTCONNECT-ADAPTER](https://github.com/JuanenRac/HYDRA-UMC-MTCONNECT-ADAPTER)** — 具备降级模式输出的真实 MTConnect `/probe` 与 `/current` XML 端点。

*辅助工具*
- **[HYDRA-UMC-DASHBOARD-AI](https://github.com/JuanenRac/HYDRA-UMC-DASHBOARD-AI)** — 基于 DATALAKE/ANOMALY-DETECTOR 的智能摘要与异常高亮面板，具备诚实的统计回退机制。
- **[HYDRA-UMC-TOOL-CLI](https://github.com/JuanenRac/HYDRA-UMC-TOOL-CLI)** — 具备真实、稳定退出码契约的车队 CLI，是 HYDRA-UMC-SERVER 自身 API 的真实在线客户端。
- **[HYDRA-UMC-WATCH](https://github.com/JuanenRac/HYDRA-UMC-WATCH)** — 带有触觉提醒模式与配对手机语音中继的 WearOS 伴侣应用(尚未在实体手表上运行)。
- **[HYDRA-UMC-CONNECTOR-HUB](https://github.com/JuanenRac/HYDRA-UMC-CONNECTOR-HUB)** — 外部适配器能力目录，设计上仅支持 GET。
- **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** — 面向板卡安装机架的固件，具备真实的工具 ID 解码与 Smart Idle 预热逻辑。
- **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** — 面向热成像/RGB 检测工具头的固件及真实 Python 视觉伴侣程序。
- **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** —— 发现、克隆并更新本生态系统中每个仓库的管理类桌面工具。
- **[HYDRA-UMC-OS-REBUILDER](https://github.com/JuanenRac/HYDRA-UMC-OS-REBUILDER)** — 从源码构建全新的 CM5 镜像，是 "Ecosystem Operations" 系列的另一个兄弟项目。

## 📚 文档

更多阅读：

* **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — 各部分、一次事件的流程，以及节点止步之处。
* **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** — 配置文件的每个开关和每个可调的值。
* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — 每个命令、退出码和配方的格式。
* **[docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md)** — 节点遵守的规则以及未覆盖的内容。
* **[docs/PANEL_CONTRACT.md](docs/PANEL_CONTRACT.md)** — 面向仪表板和工作室的状态文档。
* [生态系统的安全基线](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md)
* [生态系统的威胁模型](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md)
* [本仓库的更新日志](CHANGELOG.md)
* [本仓库的许可证](LICENSE.md)

## 🤝 参与贡献与社区

* 提交 pull request 之前，请运行 `HYDRA_UMC_CI=1 py -3 tools/ci_validate.py`（或 `HYDRA_UMC_CI=1 python3 tools/ci_validate.py`）：它必须输出 `CI_VALIDATION=PASS`。此检查不要运行 `build.sh` 或 `build.bat`；构建不是检查。
* 八个 README 由 HYDRA-UMC-DOCS 中的同一个源生成；请勿手工编辑。修改源文件，再用 `tools/make_readmes.py` 重新生成。
* 不要在 README 中声称尚未运行过的内容：属实时请写“仅模拟”或“尚未在硬件上试过”。
* 请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)、[行为准则](CODE_OF_CONDUCT.md)、[SECURITY.md](SECURITY.md) 和 [SUPPORT.md](SUPPORT.md)。

## 👤 作者

**JuanenRac (Electro Hobby 3D)** · electrohobby3d@gmail.com

## 📜 许可证

GPL-3.0-or-later - [LICENSE](LICENSE).
