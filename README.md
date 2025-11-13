# Sora2 Prompt MCP Server

重要声明：本仓库不再提供任何安装/生成脚本；请按照 `docs/MCP.md` 的“手动配置”章节进行客户端配置（Trae/Cherry）。

一个遵循 MCP（Model Context Protocol）标准的 stdin/stdout 服务器，提供中文剧本文本到 Sora2 指令（shots JSON）的解析工具 `sora2.agent.generate`。

- 主要功能：角色识别、O.S./VO 判定、摄影机与表演建议、台词抽取与排序。
- 适配 Trae：支持 `initialize`、`notifications/initialized`、`tools/list`、`tools/call` 四个 JSON-RPC 方法。

## 安装与环境
- 需要 Python 3.11+。
- Windows 11 建议设置环境变量：`PYTHONIOENCODING=utf-8`。

### 客户端手动配置
手动配置请参考 `docs/MCP.md` 的“手动配置”章节（涵盖 Trae 与 Cherry），本 README 不再重复示例以避免冗余与漂移。


## 使用方法

### JSON-RPC（推荐）
在 Trae MCP 面板依次发送：
```
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"Trae","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"sora2.agent.generate","arguments":{"text":"示例文本","default_seconds":"4"}}}
```
返回 `tools/call.result.content[0].text` 为 JSON 字符串，包含 `shots` 数组。

#### 描述写作规范（Do / Don't）
- Do：将 `description` 写成“中文镜头导语（转换重写，非原文照搬）”，包含景别/主体/动作/情境。例如：
  - 对话：`近景特写张三，他急促喊：快跑！`
  - 旁白：`旁白（VO）：雨夜里，路灯残影在水面摇晃。`
  - 画外音：`画外音（O.S.）——李四：这边！`
- Don't：直接复制原文或仅粘贴台词。例如：
  - `快跑！`（缺少镜头导语与主体）
  - `张三说：“快跑！”`（未转换为镜头描述，仅复述原句）

### 一键处理示例文本
将 `tests/测试文稿.md` 处理并保存到 `tests/shots_测试文稿.json`：
```powershell
$t = Get-Content "tests/测试文稿.md" -Raw
Write-Output (@"{""jsonrpc"":""2.0"",""id"":3,""method"":""tools/call"",""params"":{""name"":""sora2.agent.generate"",""arguments"":{""text"":""$t"",""default_seconds"":""4"",""narration_limit"":""3""}}}@") | python -m src.mcp_server > tests/shots_测试文稿.json
```

### CLI（直接调用，不经 MCP）
```powershell
python -m src.sora2_agent --text_file tests/测试文稿.md --seconds 4 > tests/shots_测试文稿.json

### 旁白控制（无对话 → 旁白 VO）
- 当输入文本中不存在引号台词或“角色: 引号台词”结构时，解析器会切换到旁白模式，将文本按句切分并生成旁白镜头。
- 可选参数 `narration_limit`（默认 `3`）用于限制旁白分句生成的镜头数量，避免过多镜头。
- 在 MCP `tools/call` 的 `arguments` 中传入 `narration_limit`，或在不传时使用默认值。

### 强制旁白模式（单口讲故事）
- 可在 `arguments` 中传入 `mode: "narration"`，无论是否存在引号或疑问/感叹标点，均按旁白 VO 生成，适用于“单人画外讲述”的视频类型。
- CLI 同样支持：
  - `python -m src.sora2_agent --text_file tests/测试文稿.md --seconds 4 --narration_limit 3 --mode narration > tests/shots_测试文稿.json`
```

## 目录结构
- `src/mcp_server.py`：MCP 服务器（stdin/stdout）。
- `src/mcp_tool.py`：工具入口，封装 `sora2_agent`。
- `src/sora2_agent.py`：核心解析逻辑（正则、候选人名、O.S./VO、摄影机/表演建议）。
- `docs/MCP.md`：协议与使用说明。
- `docs/DEVELOPMENT.md`：开发文档（架构、扩展、测试）。
- `docs/QUICKSTART.md`：5 分钟快速上手。
- `docs/openspec.md` / `docs/openspec_generated.md`：OpenSpec手写版与工具生成版。
- `tests/`：示例与用例。

## 常见问题
- PowerShell 中直接管道中文到 JSON 可能因引号编码报 `-32700`；推荐用 Trae 的 JSON-RPC 面板或 `-Raw` 读取后拼装 JSON。
- `tools/list` 的 `nextCursor` 无分页时返回空字符串 `""`，避免严格校验报错。

```mermaid
sequenceDiagram
    participant Trae
    participant MCP as MCP Server
    participant Tool as Sora2 Agent
    Trae->>MCP: initialize / notifications/initialized / tools/list
    MCP-->>Trae: capabilities & tools
    Trae->>MCP: tools/call (sora2.agent.generate)
    MCP->>Tool: generate(payload)
    Tool-->>MCP: {shots: [...]} 
    MCP-->>Trae: {content:[{text:"{\"shots\": [...] }"}], isError:false}
```

## 许可证
本项目示例文件与文档仅用于演示与学习，若需商用请自行评估与合规。
## 构图偏好与 Fallback（不可拆分多人场景）
当 `composition_policy=mono` 或 `mono_or_empty` 时：
- 优先单主体或空镜；中文 `description` 避免“众人/两人/群像”等措辞。
- 旁白（VO）可使用空环境 B-roll / montage。
- 若文本确实表达“多人一起”且不可拆分为多个单人镜头，采用低一致性 Fallback：
  - 英文 cinematography 推荐：
    - `Extreme wide establishing; partial framing on lower bodies/feet, subjects distant`
    - `Extreme wide establishing; silhouette framing, subjects distant`
    - `Back view framing; high angle, subjects distant`
    - `Partial framing on hands/shoulders; wide, subjects distant`
    - `Skyline establishing; ambient-only emphasis; subjects implied, not emphasized`
  - 中文 description 推荐：
    - 远景或局部特写脚步，画面内齐声说：{台词}
    - 极远景剪影或背影，不强调人数，画面内齐声说：{台词}
    - 局部特写手部或肩部，画面内齐声说：{台词}
    - 城市天际线远景，声音保留，画面内齐声说：{台词}
    - 环境空镜与物件特写，声音保留，画面内齐声说：{台词}

示例：
- 输入：“他们齐声喊：上！” → description：“极远景剪影或背影，不强调人数，画面内齐声说：上！”；cinematography：`Extreme wide establishing; silhouette framing, subjects distant`。
- 输入：“同学们围在一起说：稳住！” → description：“局部特写手部或肩部，画面内齐声说：稳住！”；cinematography：`Back view framing; high angle, subjects distant`。

```mermaid
flowchart TD
    A[输入文本] --> B{composition_policy 是 mono/mono_or_empty?}
    B -- 否 --> Z[按常规生成规则]
    B -- 是 --> C{不可拆分的多人场景?}
    C -- 否 --> D[单主体镜头]
    C -- 是 --> E{语气为旁白 VO?}
    E -- 是 --> F[环境空镜/B-roll/Montage]
    E -- 否 --> G[Fallback: 远景/局部（剪影/背影/手部/肩部/天际线/脚步）]
    G --> H[中文描述加“画面内齐声说：{台词}”]
    H --> I[审查：避免“群像/两人/众人”等措辞]
```

## 相邻镜头避免重复（Diversity）
- 相邻镜头至少在景别/机位/主体局部/运动中变化一项，避免视觉重复。
- 英文 cinematography 可在后一个镜头追加不同的修饰词：`static locked-off` / `slow lateral pan` / `slow push-in` / `subtle handheld` / `tilt up/down`。
- 中文 description 同步追加动作提示：`（画面静态锁定）/（镜头缓慢横移）/（镜头缓慢推入）/（轻微手持晃动）/（镜头轻微上/下摇）`。

## 分支策略
- 当前不合并至主分支，维持“当前工作分支”为默认开发分支，持续迭代本功能。
- 待业务确认后，再准备合并与打版本标签（CHANGELOG 同步）。