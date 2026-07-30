# CodeForge:archive — 收尾阶段

## 目标

验证代码实现和规格文档的一致性，通过原生 skill 归档变更，完成整个开发周期。

## 前置检查

确认 apply 阶段已完成：

- `openspec/plans/` 下的计划文件所有步骤已勾选
- 测试全部通过（或 test_command 为 null）
- 代码审查无 Critical 问题
- `.codeforge-state.yaml` 的 checkpoint 为 `apply-done`、`consistency-verified`、`archived` 或 `done` 之一

如果前置条件不满足：自动路由时，按计划、测试和审查的实际证据把 `.codeforge-state.yaml` 修正为 `phase: apply` 和最近一个可证明的 checkpoint，然后返回 `REROUTE`；用户明确指定 archive 时返回 `NEEDS_USER`，说明未满足的前置条件并推荐先回到 apply。

## 阶段流程

### 1. 规格一致性验证

逐项检查代码实现是否和规格文档一致。这是 CodeForge 特有的验证环节，确保实现没有偏离设计。

**做法：**
- 读取 `openspec/changes/<变更名>/design.md`，逐一确认其中定义的技术方案是否在代码中体现
- 读取 `openspec/changes/<变更名>/specs/` 下的规格增量文件，确认每个 ADDED/MODIFIED/REMOVED 标记对应的代码变更确实存在
- 读取 `openspec/changes/<变更名>/tasks.md`，确认所有任务已完成
- 将验证结果整理为一份清单，逐项标注「通过」或「不一致」

验证维度：
- design.md 中定义的技术方案是否全部实现
- specs/ 中标记的 ADDED/MODIFIED/REMOVED 是否在代码中体现
- tasks.md 中的任务是否全部完成

**持久化验证状态**：验证完成后，在 `openspec/changes/<变更名>/` 下创建 `.close-verification-done` 文件（内容为验证结果清单），用于断点恢复时判断是否需要重跑验证。

完成后更新 `.codeforge-state.yaml`：`checkpoint: consistency-verified`。

### 2. 处理不一致

如果验证发现不一致，通过 `CODEFORGE_RESULT.report` 逐项列出，并返回 `NEEDS_USER` 让用户选择：

**选项 A：改代码**
- 标记哪些代码需要修改
- 询问用户是否在本阶段直接修复（简单修复）或回到 apply 阶段（复杂修复）
- 如果用户选择回到 apply 阶段：更新 `.codeforge-state.yaml` 为 `phase: apply, checkpoint: reviewed`，返回 `REROUTE`，由 Coordinator 启动 apply Agent

**选项 B：改规格**
- 标记哪些规格文档需要更新
- 更新 `openspec/changes/` 下的对应文件
- 重新走验证流程

**无论选择哪种修复方式，修复完成后必须：**
1. 删除 `.close-verification-done` 文件（使验证状态失效）
2. 更新 `.codeforge-state.yaml`：`checkpoint: apply-done`（回退到验证前）
3. 重新执行 Step 1 验证
4. 重新生成 `.close-verification-done`

验证结果全部通过后（或不一致项已修复并重新验证通过），进入 Step 3。

### 3. 调用 openspec-archive-change 归档

调用原生 `openspec-archive-change` skill，通过 CLI 执行归档。

**做法：**

1. 通过 `CODEFORGE_RESULT.report` 展示 Step 1 的验证结果。除非用户已声明自主执行或 `confirmed_answers` 已包含本次归档确认，否则返回 `NEEDS_USER` 询问是否归档，并停止当前 Agent。
2. 用户确认后宣布："调用 openspec-archive-change 归档变更"。
3. 使用 Skill 工具调用 `openspec-archive-change`，args 格式：`<变更名>；用户已在 CodeForge Coordinator 确认归档，请勿再次直接提问`。
4. `openspec-archive-change` 会自动执行：
   - 检查 artifact 完成状态（通过 CLI）
   - 检查 task 完成状态（读 tasks.md）
   - 评估 spec sync 状态（对比 delta specs 和主规格库）
   - 执行归档：`mv openspec/changes/<name> openspec/changes/archive/YYYY-MM-DD-<name>`
   - 展示归档摘要
5. 等待 skill 完成后，确认归档成功：检查 `openspec/changes/archive/` 下是否有对应目录，且原活跃变更目录已移除。

**交互边界：** `openspec-archive-change` 如果仍提出确认或其它问题，阶段 Agent 必须把问题转换为 `NEEDS_USER` 交回 Coordinator；不得在阶段 Agent 或下层 skill 上下文中直接调用用户交互工具。Coordinator 回传答案后恢复同一 archive Agent。

**降级方案：** 如果 `openspec-archive-change` skill 不可用（Skill 工具返回 "Unknown skill"），**或 `openspec archive` CLI 卡在交互式确认（Y/n）、或因 spec 未用 `## ADDED/MODIFIED Requirements` delta 头被判"无 delta"无法自动合并规格**，手动执行归档操作：
1. 确认 `openspec/changes/<变更名>/tasks.md` 中所有任务已标记为完成
2. 运行 `mkdir -p openspec/changes/archive` 确保归档目录存在
3. 运行 `mv openspec/changes/<变更名> openspec/changes/archive/$(date +%Y-%m-%d)-<变更名>` 执行归档
4. 确认归档成功：活跃变更目录已移除，archive 目录已创建

> **注**：openspec 1.3.1 的 `archive` 是交互式的，并要求 spec 用 `## ADDED/MODIFIED/REMOVED Requirements` delta 头（而非 `### Requirement:`）；不符会提示"无 delta"（非阻塞警告）。若规格未自动合并到 `openspec/specs/`，归档仍可经手动 `mv` 完成（知识图谱仅依赖归档目录的文件，不依赖 specs 合并）。

完成后更新 `.codeforge-state.yaml`：`checkpoint: archived`。

### 4. 分支收尾 + 总结

**如果仍保留整个 change 的长期 worktree：**

`subagent-implement` 创建的执行单元级临时 worktree 应已在 apply 阶段清理，不进入这里的分支处理。
通过 `NEEDS_USER` 提示用户选择分支处理方式，并给出推荐选择：

1. **合并到主分支** — 在 worktree 中合并，清理 worktree
2. **创建 PR** — 推送到远程，创建 Pull Request
3. **保持现状** — 保留分支和 worktree，稍后处理
4. **丢弃** — 放弃所有改动（需输入 "discard" 确认）

**如果没有长期 worktree（直接在当前分支开发）：**
跳过分支处理，通过 `NEEDS_USER` 询问用户是否需要提交代码。

**总结报告：**
通过 `CODEFORGE_RESULT.report` 向用户报告本次变更的完整信息：
- 完成了哪些任务
- 涉及哪些文件的改动
- 规格更新了什么
- 归档位置

**清理状态文件：**
更新 `.codeforge-state.yaml`：`checkpoint: done`。使用 `git rm .codeforge-state.yaml` 将其从 git 追踪中移除，然后 commit（message: `chore: codeforge <变更名> 完成`）。确保工作区干净，最后返回 `DONE`；即使状态文件已删除，返回结果仍必须包含上述完整摘要和归档位置。

## 出口条件

- 实现和规格一致（验证通过）
- 变更已归档（由 openspec-archive-change 完成）
- 如仍有长期 worktree：用户已选择分支处理方式且 worktree 已处理
- 如无长期 worktree：代码已提交或用户已确认稍后处理
- `.codeforge-state.yaml` 已删除

## 断点恢复

archive 阶段可能通过两种方式进入：
1. apply 阶段完成后自动进入（正常路径）
2. 用户显式指定「归档收尾」进入（用户意图覆盖）

重新运行时，读取 `.codeforge-state.yaml` 的 checkpoint 并验证：

| checkpoint | 实际状态验证 | 恢复到 |
|-----------|-------------|--------|
| `apply-done` | `.close-verification-done` 不存在 | Step 1（验证） |
| `consistency-verified` | `.close-verification-done` 存在且归档目录不存在 | Step 3（归档） |
| `consistency-verified` | `.close-verification-done` 不存在（被手动删除） | Step 1（重跑验证） |
| `apply-done` | `.close-verification-done` 存在（与 checkpoint 不一致，以文件为准） | 检查归档目录是否存在，存在则 Step 4，不存在则 Step 3 |
| `archived` | 归档目录存在但分支未处理 | Step 4（分支收尾） |
| `archived` | 归档目录不存在（归档中断） | Step 3（重做归档） |
| `archived` | 归档目录存在且分支已处理 | 展示变更摘要（同 Step 4 总结报告），然后清理状态文件完成 |

**异常状态检测：**
- 活跃变更目录已删除但 archive 目录不存在 → 归档过程中断，返回 `BLOCKED`，并在 `recovery` 中提示运行 `openspec list --json` 检查状态
- `.codeforge-state.yaml` 存在但活跃变更目录不存在且未归档 → 可能是手动删除，返回 `NEEDS_USER` 让用户确认实际状态

## 硬门

本阶段如果发现需要改代码，简单的修复可以直接做（不影响规格的 bug 修复）；但如果改动会影响规格定义，必须回到 apply 阶段。
