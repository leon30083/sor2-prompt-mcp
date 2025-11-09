# OpenSpec 项目规划：sora2-agent

- 项目描述：一个将用户输入的中文原始剧情文本（包含人物、动作、对话）自动转换为符合“Sora2视频指令格式”的智能体。输入为纯文本，输出为JSON列表，每个元素是一个镜头（shot），字段包括：shot_id、description、api_call.seconds、cinematography、performance、dialogue{character,line,tone}。
- 技术栈：Python（标准库），无外部依赖。
- 实现方式：
  - 规则引擎版：`src/sora2_agent.py`
  - LLM提示词版：`prompts/sora2_llm_prompt.md`
- 可交付物：Python函数、LLM提示词、说明文档与案例。
- 复杂度：中。

目录计划：
- docs/openspec_project.md（本文件）
- docs/openspec.md（规格说明）
- src/sora2_agent.py（核心函数）
- prompts/sora2_llm_prompt.md（提示词）
- 原始资料.md（使用说明与案例）