# 快速上手（中文版）

5 分钟完成安装与验证，适合第一次使用本项目的同学。

## 1. 环境准备
- 安装 Python 3.11+。
- Windows 11 建议设置环境变量：`PYTHONIOENCODING=utf-8`。

## 2. 启动 MCP 服务器（Trae）
在 Trae 的设置中添加：
```json
{
  "mcpServers": {
    "sora2": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

## 3. 查看工具列表
在 MCP 面板发送：
```
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
```
应返回包含 `sora2.agent.generate` 的工具列表，且 `nextCursor` 为 `""`。

## 4. 处理文本
示例：将 `tests/测试文稿.md` 转换为 shots JSON。
```
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"sora2.agent.generate","arguments":{"text":"示例中文文本","default_seconds":"4"}}}
```
结果在 `result.content[0].text`，是包含 `shots` 的 JSON 字符串。

## 5. 常见问题
- 若报 `-32700`（JSON 解析失败），检查引号与中文转义，或使用 Trae 面板直接发送而非 PowerShell 拼接。
- 若客户端严格校验 `nextCursor` 类型，请确认其为空字符串 `""`。

```mermaid
flowchart LR
  A[Trae] --> B[mcp_server]
  B --> C[sora2_agent]
  C --> B --> A
```
## 描述写作规范（Do / Don't）
- Do：将 `description` 写成“中文镜头导语（转换重写，非原文照搬）”，包含景别/主体/动作/情境。例如：
  - 对话：`近景特写张三，他急促喊：快跑！`
  - 旁白：`旁白（VO）：雨夜里，路灯残影在水面摇晃。`
  - 画外音：`画外音（O.S.）——李四：这边！`
- Don't：直接复制原文或仅粘贴台词。例如：
  - `快跑！`（缺少镜头导语与主体）
  - `张三说：“快跑！”`（未转换为镜头描述，仅复述原句）