---
name: code-forge
description: 是一套规格驱动 + 工程纪律的完整开发工作流程。它会协调 OpenSpec（规格管理）和多个研发 skills，走完从需求、实现到归档的研发全流程。当用户说「用 code-forge」「规格驱动开发」「完整流程开发功能」时触发。
disable-model-invocation: false
---

# CodeForge

CodeForge 是一个薄 Coordinator。它只负责公共前置检查、状态验真、阶段路由、Agent 生命周期和用户交互转发；`propose`、`apply`、`archive` 的实际流程分别由独立阶段 Agent 执行。

## 唯一真值

| 内容 | 唯一规则来源 |
|---|---|
| Coordinator、状态路由、Agent 交接 | 本文件 |
| propose 阶段 | [propose.md](propose.md) |
| apply 阶段 | [apply.md](apply.md) |
| archive 阶段 | [archive.md](archive.md) |

`.codex/agents/` 与 `.claude/agents/` 下的文件只是平台适配器，不得复制或改写上述流程。阶段 Agent 必须先完整读取本文件的“阶段 Agent 接口”，再完整读取对应阶段 Markdown。Agent 交接、用户交互、状态校准和结果返回以本文件为准；阶段内部流程、门禁、断点恢复和出口条件以对应阶段 Markdown 为准，适配器不得覆盖二者。

## Coordinator 职责

Coordinator 只做以下事情：

1. 只读检查 OpenSpec、`.codeforge-state.yaml` 和实际文件，只推导应启动的目标阶段。
2. 按当前平台启动对应阶段 Agent；三个阶段必须顺序执行，同一时刻不得并发启动多个阶段 Agent，但 apply 阶段内部的执行单元并行不受此限制。
3. 转发阶段 Agent 提出的单个用户问题，并把答案交回同一 Agent。
4. 在阶段 Agent 返回 `DONE` 后独立核对阶段出口；通过则继续下一阶段，不通过则恢复当前阶段 Agent。
5. 将阶段 Agent 返回的用户可见摘要展示给用户，但不把阶段内部推理或大段工作记录搬回主会话。

Coordinator 不执行阶段步骤，不调用阶段内部 skill，不写 `.codeforge-state.yaml`，也不修改业务代码。详细结果必须落在状态文件、OpenSpec artifacts、计划、报告或 Git 历史中；面向用户的简洁阶段摘要通过 `CODEFORGE_RESULT.report` 返回。

## 前置检查

只读检查项目根目录是否有 `openspec/`，仅用于确定是否必须路由到 propose。初始化 OpenSpec 和项目分析都属于 propose 阶段，由 propose Agent 按 `propose.md` 执行；propose Agent 会自行复查目录是否存在。

## 阶段 Agent

| phase | Codex agent type | Claude Code agent |
|---|---|---|
| `propose` | `codeforge_propose` | `codeforge-propose` |
| `apply` | `codeforge_apply` | `codeforge-apply` |
| `archive` | `codeforge_archive` | `codeforge-archive` |

启动阶段 Agent 时使用独立上下文，但不要为阶段 Agent 启用平台级 worktree isolation。使用以下输入包，不依赖主会话中的隐式上下文：

```yaml
CODEFORGE_CONTEXT:
  repo_root: <仓库根目录>
  routed_phase: propose | apply | archive
  route_reason: automatic | user-requested
  user_request: <用户原始请求>
  confirmed_answers: [<此前已确认的全部用户答案>]
  state_file: .codeforge-state.yaml
```

阶段 Agent 在执行阶段步骤前必须重新检查实际文件，并按对应阶段 Markdown 的断点恢复规则推导最近一个可证明的 checkpoint。目标阶段正确但状态过期时，由阶段 Agent 写入 `.codeforge-state.yaml` 后继续；自动路由下实际文件支持另一个阶段时，阶段 Agent 先持久化最近一个可证明的 phase/checkpoint，再返回 `REROUTE`。`route_reason: user-requested` 时不得仅因自动路由结果不同而改道，但仍须验证指定阶段的前置条件。无法唯一判断 active change 时返回 `NEEDS_USER`，无法证明安全恢复点时返回 `BLOCKED`。Coordinator 始终不写状态文件。

若阶段内部需要实现者或审查者，由阶段 Agent 按对应 Markdown 和被调用 skill 的规则继续分派。平台必须允许两层 Agent 深度：Coordinator -> 阶段 Agent -> 执行/审查 Agent。实现者必须能写入分配给它的 worktree，审查者必须保持只读；平台无法提供所需深度或权限时返回 `BLOCKED`，不得静默改用另一种执行模式或把未执行工作报告为完成。

## 阶段 Agent 接口

阶段 Agent 每次运行到“阶段完成”“需要重新路由”“需要用户决定”或“无法继续”即停止。阶段文档以及其调用的下层 skill 中的所有询问、确认和选择，都不得在阶段 Agent 上下文中直接调用用户交互工具，而要通过以下结果交回 Coordinator：

```yaml
CODEFORGE_RESULT:
  status: DONE | REROUTE | NEEDS_USER | BLOCKED
  phase: <返回结果的阶段 Agent；propose | apply | archive>
  checkpoint: <状态文件中已持久化的 checkpoint，或 none>
  summary: <不超过一句话>
  next_phase: <仅 REROUTE；propose | apply | archive>
  question: <仅 NEEDS_USER；一次只写一个问题>
  recommendation: <仅 NEEDS_USER；给出推荐答案及理由>
  blocker: <仅 BLOCKED；写明失败条件>
  recovery: <仅 BLOCKED；写明继续所需条件>
  report:
    - <可选；最多 8 条需要展示给用户的简洁阶段摘要>
  evidence:
    - <最多 3 个仓库相对路径、commit 或命令结果摘要>
```

状态含义：

- `DONE`：对应阶段 Markdown 的出口条件已满足，状态文件已推进到下一 phase；archive 完成时状态文件已按规则删除。
- `REROUTE`：实际文件证明应进入另一个阶段；阶段 Agent 已把状态修正到最近一个可证明的 phase/checkpoint，但没有执行当前阶段的后续步骤。
- `NEEDS_USER`：只包含一个必须由用户作出的决定。返回前持久化已完成工作，但不得越过当前 checkpoint。
- `BLOCKED`：存在无法自行改变的失败条件。必须写清已检查内容和可恢复条件，不能静默跳过。

Coordinator 对结果的处理：

- `NEEDS_USER`：向用户原样提出 `question` 和 `recommendation`；得到答案后恢复同一阶段 Agent。
- `BLOCKED`：向用户报告 `blocker`、`recovery` 和证据，停止自动推进。
- `REROUTE`：独立核对状态修正与实际文件；一致则启动 `next_phase` Agent，不一致则把缺口交回原阶段 Agent。
- `DONE`：不信任文字结论，按对应阶段 Markdown 的出口条件检查实际文件。若当前阶段不是 archive，则通过后重新读取状态并路由；若当前阶段是 archive 且出口通过，则直接结束本次 CodeForge 调用，不再重新路由。不通过则把缺口交回同一阶段 Agent。

任何状态的 `report` 非空时，Coordinator 都先向用户展示；`NEEDS_USER` 随后再提出单个问题。下层 skill 如果尝试提问，阶段 Agent 必须把该问题转换为 `NEEDS_USER`，不得让下层 skill 绕过 Coordinator。

优先恢复原阶段 Agent。平台无法恢复时，启动同类型新 Agent，并重新传入用户原始请求和全部已确认答案；新 Agent 仍须从状态文件和 artifacts 恢复。

## 状态文件

项目根目录的 `.codeforge-state.yaml` 是快速路由缓存：

```yaml
version: 1
active_change: add-user-auth
phase: propose | apply | archive
checkpoint: profiler-done | requirements-confirmed | openspec-generated | plan-generated | plan-generated-and-confirmed | unit-N-complete | task-N-complete | verified | reviewed | apply-done | consistency-verified | archived | done
project_profile:
  languages: [java]
  frameworks: [spring-boot]
  build_tool: maven
  compile_command: mvn compile
  compile_scope: full | scoped
  test_command: mvn test
  structure: single-module
  has_ci: true
```

实际文件是 ground truth，状态文件只是缓存。阶段入口、断点恢复和阶段出口都必须核对实际文件。Coordinator 只选择目标阶段；阶段 Agent 负责推导并持久化最近一个可证明的 phase/checkpoint。

## 状态检测与路由

1. 读取 `.codeforge-state.yaml`。不存在时扫描实际文件；没有可恢复变更则路由到 propose。
2. 若存在多个活跃变更且无法从 `active_change` 唯一确定目标，Coordinator 直接让用户选择，并把答案加入 `confirmed_answers`。
3. 按状态文件和实际文件选择目标阶段，但不写文件：
   - `propose`：没有与 `active_change` 绑定且含 checkbox 的计划时进入 propose；已有有效计划时进入 apply。
   - `apply`：缺少有效计划时进入 propose；计划存在且仍需实现、验证或审查时进入 apply。
   - `archive`：计划未全部完成时进入 apply；apply 出口满足后进入 archive。归档内部 checkpoint 和 `.close-verification-done` 只按 `archive.md` 判断。
4. 无状态文件但存在一个活跃变更时：无有效计划路由 propose；计划有未完成 checkbox 路由 apply；计划全部完成仍先路由 apply 做验证和审查。
5. 将目标阶段放入 `CODEFORGE_CONTEXT`，启动对应阶段 Agent；该 Agent 验证并持久化状态修正后再执行阶段步骤。

用户明确指定阶段时，跳过自动阶段选择并路由到指定阶段 Agent，但仍须检查该阶段的前置条件。满足时由阶段 Agent 把状态校准到指定阶段；不满足时返回 `NEEDS_USER` 或 `BLOCKED`，不得伪造状态或自动越过用户指定的阶段。

## 阶段出口

Coordinator 在 `DONE` 后读取对应阶段 Markdown 的“出口条件”并逐项验真：

| 完成阶段 | 必须观察到的状态 |
|---|---|
| propose | `phase: apply`、`checkpoint: plan-generated-and-confirmed` |
| apply | `phase: archive`、`checkpoint: apply-done` |
| archive | 变更已归档且 `.codeforge-state.yaml` 已删除 |

出口不满足时不得启动下一阶段。出口满足后立即重新路由；因此一次 CodeForge 调用会持续推进，直到流程完成、需要用户决定或显式阻塞。archive 完成后视为流程结束，直接终止，不再开启新一轮路由。
