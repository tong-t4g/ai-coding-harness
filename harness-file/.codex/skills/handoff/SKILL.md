---
name: handoff
description: 将当前对话压缩为交接文档，供另一个 Agent 接续工作。
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

编写交接文档，总结当前对话，使全新的 Agent 能够继续工作。将文档保存到用户操作系统的临时目录，而不是当前工作区。

在文档中包含“建议使用的 skills”部分，列出接续工作的 Agent 应调用的 skills。

不要重复其它产物（规格、计划、ADR、Issue、commit、diff）中已经记录的内容，改用路径或 URL 引用它们。

脱敏所有敏感信息，例如 API 密钥、密码或个人身份信息。

如果用户传入参数，将其视为下一次会话的工作重点，并据此定制交接文档。
