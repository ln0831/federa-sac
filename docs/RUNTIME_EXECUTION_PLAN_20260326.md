# FedGrid Runtime Execution Plan (2026-03-26)

## 1. Goal

在当前统一运行包根目录内，建立一条可重复、可检查、可交付的执行路径，最终形成两类产出：

- 数据交付：完整 suite 结果目录、聚合 CSV、LaTeX 表、图、运行日志、报告。
- 论文交付：主表、附表、消融表、主图、结果叙述骨架、方法骨架与补充材料映射。

本计划默认当前根目录就是唯一 `project_root`，不再引入外部双根结构。

## 2. Current State Snapshot

### 2.1 已验证

- `python scripts/check_runtime_bundle.py --project_root .` 通过。
- `pytest -q tests/test_v8_runner_flags.py` 通过。
- `pytest -q tests/test_v8_summary_pipeline.py` 通过。

### 2.2 当前阻塞

- 当前默认 Python 是 `3.13.2`。
- `pytest -q tests` 失败，原因是缺少 `torch`。
- 环境文档建议使用 `conda` + Python `3.11`，当前解释器与建议环境不一致。

### 2.3 已有历史资产

- 运行规范与事实源：
  - `README_UNIFIED_RUNTIME_BUNDLE.md`
  - `docs/VERSION_MAP_AND_SOURCE_OF_TRUTH.md`
  - `docs/EXPERIMENT_RUNBOOK.md`
  - `docs/RESULTS_CHECKLIST.md`
  - `docs/PAPER_TABLE_MAPPING.md`
  - `skills/fedgrid-runtime-runner/`
- 历史分析与论文草稿：
  - `CURRENT_RESULTS_ANALYSIS.md`
  - `FEDGRID_EXPERIMENT_MATRIX_v4.md`
  - `FEDGRID_LITERATURE_TO_CODE_MAP_v4.md`
  - `FEDGRID_PAPER_OUTLINE_v4.md`
  - `PAPER_METHOD_SKELETON.md`
- 历史运行结果：
  - `outputs/suites/case141_fedgrid_main_rr/`
  - `outputs/suites/case141_fedgrid_tune_seed2_rr_v1/`
  - `outputs/automation_logs/`

## 3. Readout of Existing Deliverables

### 3.1 当前已有数据产物

- `case141_fedgrid_main_rr` 已有：
  - `manifests/`
  - `eval/`
  - `agg/`
  - `reports/fedgrid_v6_report.md`
  - `reports/latex/*.tex`
  - `reports/figures/*.png`
  - `checkpoints/`
- `case141_fedgrid_tune_seed2_rr_v1` 已有同类结构，但主要是单 seed 调参结果。

### 3.2 当前已有论文产物

- 论文骨架和方法骨架已存在。
- 主表/附表/消融表导出链已存在。
- 图导出链已存在。
- Markdown 结果报告已存在，可作为论文结果段落底稿。

### 3.3 当前不足以直接形成最终“数据 + 论文”交付的点

- 缺完整环境闭环：训练依赖未安装，完整测试未跑通。
- 缺完整 preset 闭环：当前只看到 `main` 和 `tune_seed2` 类结果，没有看到完整 `ablation`、`robustness`、`full` 套件交付。
- 缺结果定稿门槛：当前已有 `main` 报告中，`fedgrid_topo_proto` 和 `fedgrid_v4_cluster_distill` 在 `random_reset` 上的 paired return 为负，不适合直接包装成论文主结论。
- 缺 portability 清理：已有 manifest/report 中记录的 `project_root` 和 `suite_root` 指向旧路径 `C:\Users\ASUS\Desktop\fuxian\...`，正式交付前需要统一到当前 bundle 路径。
- 缺最终汇编层：当前已经有表、图、报告和提纲，但还没有一份面向投稿的统一“结果包说明 + 论文素材索引”。

## 4. Sub-agent Topology

不建议一开始就做代码大搬家。建议先按职责拆分子 agent，只做“读、验、汇、改”四类工作。

### Agent A: Orchestrator

- 维护唯一事实源。
- 记录每轮运行状态、阻塞点、下一步。
- 统一命名 `suite_name`、输出目录和交付清单。

### Agent B: Environment and Runtime Validator

- 负责环境建立、依赖补齐、预检、dry run、测试分层执行。
- 先跑轻量校验，再跑真实训练。

### Agent C: Output Auditor

- 负责检查 `manifest/eval/agg/reports` 是否齐全。
- 核验 paired metrics、同 context 对比、LaTeX 表和图是否生成。

### Agent D: Structure Refactor Agent

- 只在基线闭环后进入。
- 目标是降低根目录混杂度，不改变既有 runner 契约。
- 优先做路径规范化、模块归类、历史文档归档、输出索引化。

### Agent E: Paper Packaging Agent

- 从 `agg/`、`reports/latex/`、`reports/figures/` 和现有论文骨架中组装投稿材料。
- 负责结果叙事收紧，不直接照抄 Markdown report。

## 5. Execution Phases

### Phase 0. Freeze Source of Truth

目标：

- 明确根目录就是唯一 `project_root`。
- 明确活跃脚本：
  - `run_case141_fedgrid_v6.py`
  - `summarize_fedgrid_suite_v6.py`
  - `export_fedgrid_tables_v6.py`
  - `make_fedgrid_figures_v6.py`
  - `make_fedgrid_report_v6.py`

通过条件：

- 不再混用其他版本目录。
- 所有后续命令都从当前 bundle 根目录执行。

### Phase 1. Environment Bring-up

目标：

- 建立 `conda` Python 3.11 环境。
- 安装最小依赖和训练依赖。
- 跑通完整测试分层。

建议顺序：

1. `conda create -n fedgrid-runtime python=3.11 -y`
2. `conda activate fedgrid-runtime`
3. `pip install matplotlib pytest numpy pandas`
4. `pip install torch networkx scipy pandapower gymnasium`
5. `python scripts/check_runtime_bundle.py --project_root .`
6. `pytest -q tests/test_v8_runner_flags.py tests/test_v8_summary_pipeline.py`
7. `pytest -q tests`

通过条件：

- `check_runtime_bundle.py` 通过。
- 完整 `pytest -q tests` 通过。
- 无缺库错误。

### Phase 2. Baseline Reproduction

目标：

- 先确认 `main` preset 在当前环境可执行。
- 不做结构重构，不改核心训练/后处理逻辑。

建议顺序：

1. `main --dry_run --no_post`
2. `main --no_post`
3. `bash scripts/run_postprocess.sh python outputs/suites/case141_fedgrid_main_rr`

通过条件：

- `manifests/` 完整。
- `eval/` 下每个 compare label / seed 都有 `summary_*.csv` 和 `per_episode_*.csv`。
- `agg/` 关键文件齐全。
- `reports/latex/*.tex`、`reports/figures/*.png`、`reports/fedgrid_v6_report.md` 全部生成。

### Phase 3. Full Experiment Build-out

目标：

- 建立可用于论文的完整结果矩阵，而不是只靠现有 `main` 与单 seed 调参结果。

推荐执行顺序：

1. `ablation`
2. `robustness`
3. 资源允许时 `full`

通过条件：

- `robustness` 覆盖 dropout / Byzantine 方法。
- `ablation` 能支撑论文消融表。
- 各套件都能独立后处理成功。

### Phase 4. Result Triage

目标：

- 判断当前方法是否具备进入论文定稿的证据强度。

重点规则：

- 以 paired metrics 为主，不以 absolute metrics 直接写主结论。
- `random_reset` 作为主表，`static` 作为附录 sanity check。
- 若主方法没有稳定优于 baseline，则不能直接包装成“方法有效”。

通过条件：

- 主结果、鲁棒性、消融三块叙事一致。
- 关键指标没有自相矛盾。
- 结果报告中的 claim 能被表和图逐条回指。

### Phase 5. Structure Cleanup

这一步放在基线闭环之后，避免一边跑实验一边换目录。

优先项：

- 统一绝对路径写入策略，避免 manifest/report 继续写旧工作区路径。
- 给顶层版本化文档建立归档区，例如 `docs/archive/`。
- 把“当前活跃文件”和“历史对照文件”明确分层。
- 给 `outputs/suites/` 增加统一索引文档，记录每个 suite 的用途、状态和可用于论文的等级。

不建议在这一阶段做：

- 大规模搬迁训练脚本到新包路径。
- 修改 runner CLI 契约。
- 重写 summarize/export/figure/report 主链。

### Phase 6. Final Packaging

目标：

- 固化最终“数据 + 论文”交付。

数据交付至少包含：

- `outputs/suites/<final_suite>/manifests/`
- `outputs/suites/<final_suite>/eval/`
- `outputs/suites/<final_suite>/agg/`
- `outputs/suites/<final_suite>/reports/`
- 环境说明
- 运行命令记录

论文交付至少包含：

- 主表：`reports/latex/table_main_random_reset.tex`
- 附表：`reports/latex/table_appendix_static.tex`
- 消融表：`reports/latex/table_ablation_random_reset.tex`
- 主图：`reports/figures/random_reset_delta_*.png`
- 结果摘要：`reports/fedgrid_v6_report.md`
- 叙事骨架：
  - `FEDGRID_PAPER_OUTLINE_v4.md`
  - `PAPER_METHOD_SKELETON.md`

## 6. Validation Metrics

建议把验证分为四层。

### 6.1 环境层

- Python 版本固定为 3.11。
- `torch`、`networkx`、`scipy`、`pandapower`、`gymnasium` 已安装。
- `pytest -q tests` 全通过。

### 6.2 运行层

- `fedgrid_v6_run_matrix.csv` 完整。
- `ckpt_status_post = ready` 尽量全绿。
- `ckpt_bytes > 0`。

### 6.3 数据层

- 每个 `compare_label` / `seed` 的 `summary_*.csv` 和 `per_episode_*.csv` 成对出现。
- paired 表仅在同 context 内比较：
  - `case`
  - `outage_k`
  - `outage_policy`
  - `outage_radius`
  - `topology_mode`
- 不允许 duplicate episodes。
- 不允许 episode alignment mismatch。

### 6.4 论文层

- 主表基于 `random_reset`。
- `static` 仅作附表或 sanity check。
- `return`、`vviol`、`ploss` 的 trade-off 叙述一致。
- 如果主方法结果为负或不稳定，论文路线必须调整为：
  - 调参结果汇报
  - 失败分析
  - 或重新设计方法/超参后再重跑

## 7. Recommended Output Layout

建议把最终对外交付收口到以下位置：

- 运行数据主目录：
  - `outputs/suites/<suite_name>/`
- 汇总索引：
  - `outputs/suites/INDEX.md`
- 论文素材总目录：
  - `docs/paper_package/`

`docs/paper_package/` 里建议包含：

- `tables/`
- `figures/`
- `claims.md`
- `results_to_tables_map.md`
- `repro_commands.md`

## 8. Immediate Next Actions

按优先级执行：

1. 建立 Python 3.11 conda 环境。
2. 安装 `torch` 等训练依赖，补齐 `pytest -q tests`。
3. 跑 `main --dry_run --no_post`，确认当前环境下 runner 可出完整 manifest。
4. 如 dry run 正常，再执行 `main` 正式训练与后处理。
5. 对已有 `case141_fedgrid_main_rr` 做一次路径与结果一致性复核。
6. 在 `main` 复现稳定后，再进入 `ablation`、`robustness`。
7. 只有在基线闭环后，才开始结构优化。

## 9. Hard Constraints

- 不把重构放在首次复现之前。
- 不绕过 summarize / figure 的 fail-fast。
- 不以单 seed 调参结果当最终论文主证据。
- 不在 paired metrics 缺失时直接写论文结论。
- 不继续沿用旧绝对路径作为正式交付记录。
