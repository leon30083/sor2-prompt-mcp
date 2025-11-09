# OpenSpec规范文件（生成版）

以下内容由 OpenSpec 工具生成，作为参考规范补充：

## 生成内容
# OpenSpec规范文件

基于您的需求生成的规范：

## 需求分析
实现一个 MCP stdin/stdout 服务器，提供工具 `sora2.agent.generate`，将中文剧本文本解析为 shots JSON。输入：text 字符串，default_seconds 可选字符串；输出：{shots: Shot[]}，Shot 含 shot_id、description、api_call.seconds、cinematography、performance、dialogue{character,line,tone}。需提供 Trae 配置说明、JSON-RPC 交互示例、CLI 示例。测试：新增 10 条中文用例，run_cases.py 断言至少1条台词；CI：GitHub Actions 在 Ubuntu 上运行 tests/run_cases.py，并校验 tools/list 的 nextCursor 为空字符串。发布：打标签 v1.0.0。文档：README、MCP.md、DEVELOPMENT.md、QUICKSTART.md 含 Mermaid 图，暗黑主题可读。

## 项目类型
custom

## 识别的特性
- 暂无显式特性

## 生成的规范内容
```markdown
# API规范：自定义项目

## 项目信息
- **名称**：自定义项目
- **版本**：v1.0.0
- **描述**：根据需求生成的定制化规范
- **复杂度**：medium

## 需求摘要
- **项目类型**：custom
- **需求描述**：实现一个 MCP stdin/stdout 服务器，提供工具 `sora2.agent.generate`，将中文剧本文本解析为 shots JSON。输入：text 字符串，default_seconds 可选字符串；输出：{shots: Shot[]}，Shot 含 shot_id、description、api_call.seconds、cinematography、performance、dialogue{character,line,tone}。需提供 Trae 配置说明、JSON-RPC 交互示例、CLI 示例。测试：新增 10 条中文用例，run_cases.py 断言至少1条台词；CI：GitHub Actions 在 Ubuntu 上运行 tests/run_cases.py，并校验 tools/list 的 nextCursor 为空字符串。发布：打标签 v1.0.0。文档：README、MCP.md、DEVELOPMENT.md、QUICKSTART.md 含 Mermaid 图，暗黑主题可读。

## 识别的特性
- 暂无显式特性

## 核心功能模块
- 此处保留为工具生成的模板内容，供参考。
```

## 使用方式
- 作为补充参考规范，与 `docs/openspec.md` 一起使用。