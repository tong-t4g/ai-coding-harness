将 openspec 的安装集成到 ai-coding-harness 的安装过程中
openspec 和 开发流程 能不能结合 /goal 使用？
有哪些环节是要加在 hooks 中的？
整理下整个开发流程可以独立成哪些部分。
Grill-me（matt-pocock-skills） 可以对需求/任务进行思考和提问，这个很有用，这种方式是不是能替代对需求的评审？   https://mp.weixin.qq.com/s/hyY3ZGuzr4YFEwQi0YrCXA
Trellis 应该是集大成者，吸收了superpower openspec 的能力和设计，但又更简单，轻量
spec-superflow 直接就是融合了 superpower openspec 的代码
加入需求评审（proposal.md、spec.md 是需要评审的）、设计评审 、对抗性评审 skill(用subagent 调用，以保持独立性)
是否可以，是否必要加一个调度 agent，负责执行整个流程？有必要，可以将流程串成更长更自动化的大流程，一些消耗context window 的操作得独立成 subagent
加一个让 AI 把值得更新到 docs 中的知识更新到合适位置（主要是一些架构约束、隐含业务约束）的 skill 或  subagent 。在更高层的流程调用中调用。

/opsx:propose -> /opsx:apply -> /opsx:verify -> /opsx:archive
|        |                     |        |
这里要人工审核设计   这两步能不能连续执行，     这一步要手工运行，因为上一步可能反复执行多次后才能归档
并且加入其它skill