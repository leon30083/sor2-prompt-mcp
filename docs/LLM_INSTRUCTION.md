# Sora2 MCP LLM 指令与标签规范

## 指令要点
- 默认调用 `sora2.agent.generate.auto`，由后端自动判定对话/旁白。
- 明确旁白需求时，调用 `sora2.agent.generate.narration` 并传 `narration_limit`。
- 解析返回的 `meta` 字段：`chosen_mode`、`shots_count`、`parse_summary`。

## 拼接标签规范（stitch_tags）
- `audio_type`: `voice_over` | `dialogue`
- `vo_priority`: 0–100（按旁白句占比归一化）
- `dialogue_priority`: 0–100（按对话句占比归一化）
- 计算：
  - `vo_priority = round((narration_count / total_sentences) * 100)`
  - `dialogue_priority = round((dialogue_count / total_sentences) * 100)`
- `audio_type = (meta.chosen_mode == "narration") ? "voice_over" : "dialogue"`
 - 术语区分：旁白=VO（`dialogue.tone` 以 `voice-over` 开头）；画外音=O.S.（`dialogue.tone` 以 `off-screen` 开头），两者不可混用。
  - 缺省：当统计缺失或 `total_sentences=0`，两者取 0；`audio_type`照 `chosen_mode`。

## 描述写作规范（Do / Don't）
- Do：镜头导语化书写，包含景别/主体/动作/情境。例如：
  - 对话：`近景特写张三，他急促喊：快跑！`
  - 旁白：`旁白（VO）：雨夜里，路灯残影在水面摇晃。`
  - 画外音：`画外音（O.S.）——李四：这边！`
- Don't：机械复制原文或仅粘贴台词。例如：
  - `快跑！`（缺少镜头导语与主体）
  - `张三说：“快跑！”`（未转换为镜头描述，仅复述原句）

## Mermaid 流程图
```mermaid
flowchart TD
  A[收到文本] --> B{是否明确要求旁白?}
  B -- 是 --> C[调用 .narration]
  B -- 否/不确定 --> D[调用 .auto]
  C --> E[返回 shots + meta]
  D --> E[返回 shots + meta]
  E --> F{meta.chosen_mode}
  F -- narration --> G[计算 vo_priority 并行拼接]
  F -- dialogue --> H[计算 dialogue_priority 并行拼接]
  G --> I[输出成片/后处理]
  H --> I[输出成片/后处理]
```

## Mermaid 时序图
```mermaid
sequenceDiagram
  participant L as LLM
  participant M as MCP Server
  participant T as Tool Layer
  participant P as Parser

  L->>M: call .auto / .narration (text, options)
  M->>T: route to fixed mode
  T->>P: generate_sora2_instructions(text, mode)
  P-->>T: {shots, meta(chosen_mode, shots_count, parse_summary)}
  T-->>M: structured result
  M-->>L: JSON content with meta
  L->>L: 注入 stitch_tags 并行拼接
```

## 示例
- JSON-RPC `.auto`
```json
{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"sora2.agent.generate.auto","arguments":{"text":"张三说：“快跑！”","default_seconds":"3"}}}
```
- JSON-RPC `.narration`
```json
{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"sora2.agent.generate.narration","arguments":{"text":"夜色浓重，风声在巷口回旋。","narration_limit":"3"}}}
```

## 10条测试输入与预期
1. 张三说：“快跑！” → `.auto`，`chosen_mode=dialogue`，`dialogue_priority≈100`
2. 远处传来呼喊：“快躲起来！” → `.auto`，`chosen_mode=dialogue`
3. 李四大喊：“这边！” → `.auto`，`chosen_mode=dialogue`
4. 旁白：“他们以为安全。” → `.auto`（含引号），`chosen_mode=dialogue`
5. 张三问：“你看见了吗？” → `.auto`，`chosen_mode=dialogue`
6. 门外有人喊：“开门！” → `.auto`，`chosen_mode=dialogue`
7. 王五说道：“安静。” → `.auto`，`chosen_mode=dialogue`
8. 陈晓低声道：“别动。” → `.auto`，`chosen_mode=dialogue`
9. 画外音：“夜色深沉。” → `.auto`（含引号），`chosen_mode=dialogue`
10. 雨夜里，路灯残影在水面摇晃。 → `.narration`，`chosen_mode=narration`，`vo_priority≈100`