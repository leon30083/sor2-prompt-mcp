# OpenSpec 规格说明：sora2-agent

## 需求分析
- 目标：实现一个“sora2视频指令生成智能体”。
- 输入：用户中文原始文本（可能包含叙述、人物名、引号内对话、动作与场景线索）。
- 输出：JSON数组，每个元素为一个镜头，字段：
  - `shot_id`: `shot_<两位序号>_<角色或动作短语slug>`
  - `description`: 中文镜头描述
  - `api_call.seconds`: 字符串时长，默认`"4"`
  - `cinematography`: 英文机位与运动（如`Medium close-up (MCU)`）
  - `performance`: 英文表演描述
  - `dialogue`: `{ character, line, tone }`

## 功能模块
1. 文本标准化：清理空白、统一中文引号、分句。
2. 实体抽取：人物名、动词短语、场景词。
3. 对话抽取：识别中文引号内容并归属角色。
4. 要素推断：关键词映射生成 `cinematography` / `performance` / `tone`。
5. 镜头构建：封装为Sora2镜头对象，并生成连续序号与`shot_id`。
6. 输出整形：返回JSON列表；同时生成LLM提示词版本文本。

## 非功能要求
- 纯Python，无外部依赖；函数尽量小且可复用；控制圈复杂度。
- 关键词词典与映射可扩展；默认时长可配置。
- 文档含Mermaid流程图，暗黑主题可读。

## 交付物
- `src/sora2_agent.py`（Python函数）
- `prompts/sora2_llm_prompt.md`（LLM提示词模板）
- `docs/openspec.md`（本规格说明）
- 在`原始资料.md`中添加使用说明与10个案例及预期结果。

## 简要数据结构
- `Shot`：
  - `shot_id: str`
  - `description: str`
  - `api_call: { seconds: str }`
  - `cinematography: str`
  - `performance: str`
  - `dialogue: { character: str, line: str, tone: str } | None`

## 流程图
```mermaid
flowchart TD
  A[用户原始文本] --> B[文本标准化]
  B --> C[实体与对话抽取]
  C --> D[要素推断\n(机位/表演/语气)]
  D --> E[镜头构建]
  E --> F[输出JSON列表]
  F --> G[LLM提示词版本]
```

## 质量标准
- 指令字段完整率 ≥ 99%
- 生成代码无外部依赖；可读性与复用性良好。
- 词典扩展无需改动核心逻辑。