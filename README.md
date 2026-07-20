参考资料：

完整的 19 节点是一条标准研发链路：
需求评审→需求确认→方案设计→方案确认→Pre-Mortem→实施计划→验收标准确认
→拉变更→建分支→建 worktree→开发→编译→单测→ATDD→证据链
→部署预发→接口测试→上线确认→验收报告

实际流程：
主会话 → dispatcher(读 state.json，返回"下一步调谁")
→ intent-classifier 判定意图×风险
→ dispatcher → 三角色并行评审(业务/技术/质量) → orchestrator 合成 → 我确认需求
→ dispatcher → plan-generator 出技术方案
→ dispatcher → developer 按 TDD 编码
→ dispatcher → verifier 跑 G1–G8 门禁
→ dispatcher → deployer 部署预发
→ dispatcher → tester 接口测试 → 验收报告

dispatcher  intent-classifier 三角色出需求分析(业务、开发、测试) plan-generator  developer  verifier  deployer tester








完整流程：
probe(对需求进行提问)  propose  proposalreview(对proposal、spec进行评审、对抗性评审（考虑三角色）)  需求确认（人工环节） apply  codereview(独立于后一个步骤的代码审查) verify  部署测试环境（这一步始终由人工调用） archive

流程类型和状态管理：
用户可以根据需求复杂度，选择使用不同的 skill,不同的 skill 有不同的流程：
HIGH -- 
MEDIUM -- 
LOW -- 适用于明确的、少量的修改，这种修改一般比较细节，不影响业务逻辑，不需要 proposal、specs，也无需追溯。只需 implement、tdd、codereview

specs 文档的作用：
proposal.md — 需求方案/动机文档
specs.md -- 功能描述/规范
design.md -- 技术实现方案/设计文档
tasks.md -- 实现清单/任务列表



是否需要一个单独的 workflow.yaml 来定义流程？

流程状态外置（state.json,状态维护最好提供skill和脚本，确保状态维护的正确性）。门禁状态看写到同一个文件中，还是新建一个文件。门禁有：编译、单侧、部署等。门禁需要在特定环节使用hook来检查


要求：
占用context window 的步骤都使用 subagent 调用 skill 的方式

待办任务项：




Grill-me（matt-pocock-skills） 可以对需求/任务进行思考和提问，这个很有用，这种方式是不是能替代对需求的评审？   https://mp.weixin.qq.com/s/hyY3ZGuzr4YFEwQi0YrCXA  https://github.com/devcxl/mattpocock-skills-zh
Trellis 应该是集大成者，吸收了superpower openspec 的能力和设计，但又更简单，轻量  https://github.com/mindfold-ai/Trellis/blob/main/README_CN.md
spec-superflow 直接就是融合了 superpower openspec 的代码   https://github.com/MageByte-Zero/spec-superflow
HyperSpec 协调 OpenSpec（规格管理）和 Superpowers,一个很简单的工程。  https://github.com/wind7rui/HyperSpec
https://github.com/devcxl/superpowers-zh

加一个让 AI 把值得更新到 docs 中的知识更新到合适位置（主要是一些架构约束、隐含业务约束）的 skill 或  subagent 。在更高层的流程调用中调用。

有哪些环节是要加在 hooks 中的？
上下文压缩后，触发 cat 重要的规则文件。在CC 中压缩之后两层 CLAUDE.md、MEMORY.md 不会丢失，对话中的信息、skill内容、被引用的下层rules都很可能丢失。所以应该重新读取重要的下层rules。
对于规则强制检查，如必须生成单测，其实对于不同场景的 coding 没有太多普遍适用的必须要强制的检查。但在具体的业务流程中是有很多要强制检查的。
openspec 和 开发流程 能不能结合 /goal 使用？

将 ATDD 融入流程(openspec 已经遵循ATDD的思想了)

将 openspec 的安装集成到 ai-coding-harness 的安装过程中




/opsx:propose -> /opsx:apply -> /opsx:verify -> /opsx:archive
              |        |                     |        |
        这里要人工审核设计   这两步能不能连续执行，     这一步要手工运行，因为上一步可能反复执行多次后才能归档
        并且加入其它skill


真正需要警惕的不是"agent 多"，而是"agent 间耦合多"。 输入输出是清晰的文件/JSON、不需要会话协商，数量就不是问题。