# Codex Launch Prompt

将本压缩包解压后的目录作为当前项目根目录。你现在是这个开源项目的主要实现 Agent，请以高自主方式把项目推进到 `CODEX_GOAL.md` 定义的 v0.1.0 可验证完成状态。

请先执行以下启动流程：

1. 读取根目录 `AGENTS.md`、`CODEX_GOAL.md`、`START_HERE.md`、`docs/INDEX.md`、`.agent/PLANS.md`，以及当前 `.agent/exec-plans/active/` 中的 ExecPlan。
2. 不要一次性读取全部 docs；严格按照 `docs/INDEX.md` 和 active ExecPlan 只加载当前任务所需文档，控制上下文膨胀。
3. 检查本地 Git、Python、Java、Docker 等环境以及当前仓库状态。若尚未初始化 Git，可初始化本地仓库；不要擅自创建/修改远程 GitHub 仓库、Secrets、分支保护或 Release。
4. 如果当前在 `main`，创建符合仓库规范的本地工作分支后再实施修改。
5. 使用 Codex Goal 模式，把 `CODEX_GOAL.md` 作为完成合同：持续推进，只有在明确满足其中 verification surface、达到预算/中断、或遇到文档定义的真实 blocker 时停止。不要在每个小步骤后等待我确认。
6. 当前第一执行单元是 `.agent/exec-plans/active/0001-foundation-and-first-vertical-slice.md`。先完成并验证该计划，再创建后续 ExecPlan，按 `docs/50-roadmap/ROADMAP.md` 继续推进。
7. 你可以自主完成代码、测试、配置、Docker、CI、文档和本地 Git commit；保持小而有意义的 Conventional Commits。不要直接修改 `main`，不要 force push，不要发布 Release，不要进行未经授权的破坏性远程操作。
8. 遇到缺少 LLM API Key 等非结构性依赖时，不要立即停工：优先使用 deterministic fake/mock 完成架构、测试和 CI，并保留可选 live test 路径。只有没有合理本地替代且阻塞 Goal 验证时才向我提问。
9. 多智能体实现必须是真实架构能力，而非角色命名：Supervisor、Metrics/Logs/Trace specialists、Remediation、Verifier 的职责、上下文与工具权限需符合文档；独立调查尽量并行；变更类操作经过策略/HITL；执行结果必须独立验证。
10. 每完成一个重要阶段，都更新 active ExecPlan、Roadmap 的真实状态，以及 `docs/90-learning/` 下的反向学习文档。不要把未来计划写成已完成功能。
11. 在最终宣布 Goal 完成前，从干净状态重新执行 README/Makefile 所述启动、测试和至少四个场景验证，并逐条审计 `CODEX_GOAL.md` 的 completion evidence。

工作原则：优先实际实现、运行测试、修复问题和收集证据；少做无必要的长篇计划。除非出现真正需要我决策的 blocker，否则请自主选择下一项最能推进 Goal 的工作并继续。

启动后先用一段简短摘要告诉我：你读取了哪些核心文件、检测到的环境/仓库状态、当前 active ExecPlan 的目标。然后立即开始实施，不要等待我再次确认。

如果当前 Codex 版本支持 `/goal`，请将下面这条作为当前线程 Goal（必要时可在不改变语义的情况下压缩措辞）：

`/goal Deliver the Reliable Agent Lab v0.1.0 public MVP defined by CODEX_GOAL.md, verified by its clean-start, test, scenario, tracing, HITL/resume, idempotency, documentation, and CI evidence, while preserving the architecture, safety, scope, and Git constraints in AGENTS.md and the repository docs. Work through successive ExecPlans and keep iterating from test/runtime evidence until every required criterion is verified or a documented blocker makes completion impossible under the current resources.`
