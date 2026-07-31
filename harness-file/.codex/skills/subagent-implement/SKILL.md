---
name: subagent-implement
description: 执行已批准的多任务计划，将存在依赖或文件重叠的任务聚合为执行单元，为每个执行单元创建专属 Git worktree，单元内顺序实现、单元间并行，再串行集成并审查整个分支。
disable-model-invocation: true
---

# 子智能体驱动开发

用一条可恢复的闭环执行计划：**任务聚合 -> 执行单元并行实现 -> 单元审查 -> 修复复审 -> 串行集成 -> 整分支审查**。

控制器负责聚合任务、拆分上下文、创建 worktree、分派、裁定、集成和记录；实现代码始终由对应执行单元的实现者在专属 worktree 中修改并进行独立审查。

## 适用条件

仅在以下条件全部成立时使用：

1. 已有用户批准的实现计划，且任务和验收条件明确。
2. 计划完整声明每项任务的前置任务、关联文件和验收条件，足以确定执行单元。
3. 任务要在当前会话内连续执行。

任务之间可以存在依赖或修改同一文件；这类任务必须进入同一执行单元并在一个 worktree 中顺序执行。只有执行单元之间可以并行。平台并发槽不足时可以分批启动执行单元，但不得把一个执行单元拆到多个 worktree。

## 1. 建立执行上下文

1. 读取适用的 `AGENTS.md`、计划和计划引用的项目规则。
2. 确认当前分支和主工作树干净。主分支只有在用户明确同意后才能作为实现分支；计划、状态文件和已有改动必须先提交。
3. 记录分支起点 `MERGE_BASE`；它是最终审查范围的起点。
4. 解析本 skill 的安装目录，记为 `<skill_dir>`：优先使用 `$CODEX_HOME/skills/subagent-implement`；`CODEX_HOME` 未设置时，Windows 使用 `%USERPROFILE%/.codex/skills/subagent-implement`，macOS/Linux 使用 `~/.codex/skills/subagent-implement`。不得把项目根目录下的 `scripts/` 当成本 skill 的脚本目录。
5. 运行 `<skill_dir>/scripts/sdd-workspace PLAN_FILE`，取得本计划唯一的工作区路径。
6. 读取 `<工作区>/progress.md`。若文件不存在，第一行写入：
   `# SDD 进度账本 - 计划: <计划文件绝对路径>`。
7. 从账本恢复已审查、已集成执行单元和未结束的修复轮次，再为剩余任务建立待办。
8. 一次性建立任务关系图：每个未完成任务是一个节点；存在显式前置依赖，或 `关联文件` 中出现同一文件时，在两个任务间连边。比较文件前，把 `\` 转为 `/`、去掉末尾 `:行号` 或 `:起始-结束`，并使用 Git 中的仓库相对路径大小写。关联文件或依赖声明不完整时先修复计划，不得猜测并行安全性。
9. 将关系图的每个无向连通分量确定为一个执行单元。单元内按依赖拓扑顺序执行，无依赖关系时按计划编号；存在依赖环时显式 `BLOCKED`。按每个分量最小任务编号依次命名为 `unit-1`、`unit-2`。再次确认不同单元之间无依赖且无文件重叠。
10. 对全部未集成执行单元运行 `<skill_dir>/scripts/execution-worktree prepare PLAN_FILE MERGE_BASE unit-1=1,2 unit-2=3`。任务序列必须与上一步一致。脚本标准输出的唯一一行是 worktree 清单路径；从清单读取每个执行单元的任务序列和专属工作目录。

脚本是 Bash 脚本。在 PowerShell 中没有 `bash` 命令时，使用 Git Bash 的可执行文件调用；调用时传入 `<skill_dir>/scripts/<script-name>`，不得手工仿写脚本的确定性转换逻辑。

完成条件：计划路径、当前分支、`MERGE_BASE`、SDD 工作区、worktree 清单、全局约束、任务关系、执行单元和恢复位置均已确定；每个执行单元已获得一个专属 worktree，单元之间可以独立执行。

## 2. 选择子智能体

每次分派都显式选择平台支持的、能可靠完成该角色的最低能力档位：

- 规格完整、只涉及 1-2 个文件的机械任务：快速档。
- 跨文件集成、调试或需要模式判断：标准档。
- 架构决策、高风险改动和最终整分支审查：最高能力档。

平台不提供档位选择时使用默认模型，不得因此阻塞流程。尽量在同一轮中并行分派全部执行单元；超过平台并发上限时，按可用槽位分批启动。每个 worktree 同时只能有一个写入者，但不同执行单元 worktree 可以并行写入和审查。

worktree 统一由 `<skill_dir>/scripts/execution-worktree` 管理。不得再启用 Claude Code 的 `isolation: worktree`、Codex 会话级 worktree 或其它平台文件隔离，否则会产生嵌套 worktree。只启用独立子智能体上下文；平台不支持上下文隔离时使用默认行为。

## 3. 并行实现与执行单元审查

### 3.1 准备并分派

1. 将本执行单元的 `BASE` 固定为 `MERGE_BASE`，从 worktree 清单读取 `TASK_SEQUENCE` 和 `WORKDIR`。
2. 按 `TASK_SEQUENCE` 对每项任务运行 `<skill_dir>/scripts/task-brief PLAN_FILE N`，得到有序任务简报列表。脚本标准输出的唯一一行是任务简报路径。
3. 将报告路径设为同目录的 `unit-N-report.md`。
4. 使用 [implementer-prompt.md](implementer-prompt.md) 分派一个全新的实现者，传入 `WORKDIR`。仅隔离父会话上下文，不启用平台 worktree isolation。
5. 只传递有序任务简报、适用的全局约束、单元所需的既有接口与裁定、工作目录和报告路径。每项任务的精确需求只保留在对应简报中。
6. 记录实现者身份；后续修复优先恢复这个实现者。

全部执行单元的步骤 1-6 准备完成后再统一分派。完成条件：每个实现者拥有完成自身执行单元所需且仅限该单元的上下文，`BASE`、`TASK_SEQUENCE`、`WORKDIR`、简报和报告路径均已记录。

### 3.2 处理实现者状态

实现者必须返回以下状态之一：

| 状态 | 控制器动作 |
|---|---|
| `DONE` | 核对报告和测试证据，进入执行单元审查。 |
| `DONE_WITH_CONCERNS` | 正确性或范围疑虑先解决；观察性疑虑写入账本后进入审查。 |
| `NEEDS_CONTEXT` | 补充明确缺失的事实，恢复原实现者。 |
| `BLOCKED` | 改变条件后再分派：补上下文、拆任务或提升模型；计划缺陷交给用户裁定。 |

同一失败条件下不得原样重试。实现者有问题时先回答，不能用催促代替缺失信息。

完成条件：状态已被显式处理；进入审查时，报告按任务列出提交、改动摘要、测试命令、测试结果和遗留疑虑。

### 3.3 执行单元审查

1. 令 `HEAD=$(git -C WORKDIR rev-parse HEAD)`，运行 `<skill_dir>/scripts/review-package PLAN_FILE BASE HEAD <工作区>/unit-N-review.diff`。
2. 使用 [task-reviewer-prompt.md](task-reviewer-prompt.md) 分派只读审查者，输入 `WORKDIR`、有序简报列表、报告、审查包和约束当前执行单元的全局规则。
3. 审查报告必须同时给出“规格结论”和“质量结论”。
4. 对“无法从 diff 核实”的每一项，由控制器查阅计划和跨执行单元上下文；真实缺口按规格失败处理。

完成条件：每项规格要求都有结论，每项发现都有严重级别和证据，且两个审查结论均存在。

### 3.4 修复循环

规格失败、严重问题或重要问题进入修复循环。次要问题写入账本：
`执行单元 unit-N：次要问题（待最终审查）：<一句话>`。

发现与计划原文冲突时，先把发现和原文交给用户裁定。不得分派违反计划的修复，也不得用计划原文压掉真实缺陷。

每轮修复执行以下步骤，最多三轮：

1. 在执行单元 worktree 中记录 `FIX_BASE`，把全部未关闭发现原文交给原实现者；原实现者不可用或已 `BLOCKED` 时，分派新的实现者并附 `WORKDIR`、有序简报、报告和既往尝试。
2. 实现者修复、提交，重跑覆盖改动的测试，并把改动、测试文件、命令和输出追加到原报告。
3. 核对修复报告证据齐全。
4. 令 `HEAD=$(git -C WORKDIR rev-parse HEAD)`，运行 `<skill_dir>/scripts/review-package PLAN_FILE FIX_BASE HEAD <工作区>/unit-N-fix-R-review.diff`，使用 [re-review-prompt.md](re-review-prompt.md) 在同一 `WORKDIR` 做范围复审。
5. 未解决发现和修复引入的严重、重要问题进入下一轮；次要问题写入账本。
6. 追加账本：`执行单元 unit-N：修复轮次 R/3（已解决 X，未解决 Y，提交 a..b）`。

第三轮后仍有规格缺口、严重问题或重要问题时，追加
`执行单元 unit-N：BLOCKED - <未解决问题>`，向用户报告修复历史并停止。不能把它记为完成。

完成条件：规格通过、质量通过、所有严重和重要问题已关闭，且所有次要问题已进入账本。

### 3.5 记录执行单元审查通过

在同一检查点更新待办和账本：
`执行单元 unit-N（任务 1,2）：worktree 审查通过（提交 base..head，规格通过，质量通过，待集成）`。

此时不得更新计划 checkbox 或 `.codeforge-state.yaml`。其它执行单元无需等待即可继续；上下文压缩后，以账本、worktree 清单和对应 worktree 的 `git log` 为准，不重新分派已审查执行单元。

## 4. 串行集成

全部执行单元的 worktree 审查通过且没有 `BLOCKED` 后，按执行单元编号依次集成：

1. 确认主工作树干净，运行 `<skill_dir>/scripts/execution-worktree integrate PLAN_FILE unit-N`。脚本使用 `cherry-pick --no-commit` 暂存执行单元 worktree 的全部提交；冲突时保留现场并显式 `BLOCKED`，不能自动解决。
2. 运行计划要求的编译检查。失败说明执行单元独立性判断或跨单元组合有误；保留当前集成现场并显式 `BLOCKED`。
3. 将计划文件中该执行单元包含的所有任务 checkbox 更新为已完成，并把共享状态文件更新为 `checkpoint: unit-N-complete`。
4. 把执行单元代码、计划和状态文件提交为一个最终执行单元 commit。
5. 运行 `<skill_dir>/scripts/execution-worktree record PLAN_FILE unit-N HEAD`，记录该执行单元的集成提交，并追加账本：`执行单元 unit-N：已集成（提交 <sha>）`。
6. 主工作树恢复干净后才可集成下一个执行单元。

断点恢复时，若主工作树因 `integrate` 留有暂存改动，不得再次运行 `integrate`；先核对执行单元差异并完成步骤 2-5。若最终执行单元 commit 已存在但清单尚未记录，直接补跑 `record`。

完成条件：所有执行单元均按编号集成；每个执行单元在最终分支上只有一个包含代码、计划和状态的 commit；主工作树干净。

## 5. 最终整分支审查(注意！此步骤废弃，不执行)

1. 确认所有执行单元均有完成记录、所有计划任务已勾选且没有 `BLOCKED`。
2. 运行 `<skill_dir>/scripts/review-package PLAN_FILE MERGE_BASE HEAD`。
3. 使用最高能力档和 [final-reviewer-prompt.md](final-reviewer-prompt.md) 分派只读审查者，输入完整计划、审查包、进度账本和项目规则。
4. 最终发现按同一严重级别处理。每轮把全部未关闭问题交给一个修复者，修复后做范围复审，最多三轮。
5. 三轮后仍有规格缺口、严重问题或重要问题时，显式报告 `BLOCKED`。
6. 审查和计划验证全部通过后，运行 `<skill_dir>/scripts/execution-worktree cleanup PLAN_FILE` 清理执行单元 worktree。清理失败必须报告，不能把流程记为完成。

完成条件：最终规格和质量结论均通过；所有严重、重要问题已关闭；每个次要问题都有“修复”或“接受风险”的明确结论；计划要求的验证均有命令和结果证据；所有执行单元 worktree 已清理。

## 硬性边界

- 每个执行单元 worktree 同时只能有一个实现者写入；实现者不得写入其它执行单元 worktree 或主工作树。
- 单元内任务必须按 `TASK_SEQUENCE` 顺序执行；不同执行单元的实现与审查可以并行，主工作树集成必须按执行单元编号串行。
- 实现者不得修改共享计划、状态文件或进度账本；这些文件只由控制器在集成时更新。
- 不得使用平台 worktree isolation；执行单元 worktree 只能由 `<skill_dir>/scripts/execution-worktree` 创建和清理。
- 审查范围始终使用记录的 `BASE..HEAD`；`HEAD~1` 不能替代执行单元起点。
- 实现者自审不能替代独立执行单元审查。
- 任何发现都必须被修复、记录为次要问题，或以 `BLOCKED` 暴露；不存在静默丢弃路径。
