# FedGrid Unified Runtime Bundle v1

这是一个**真正可训练/可评测/可汇总**的统一运行包。

它把三部分收口到同一个项目根目录：

- **训练与评测底座**：来自 `fedgrid_refactor_v4`
- **稳定实验编排 runner**：来自经 review 修补后的 `v8.1` / `v8.2` `run_case141_fedgrid_v6.py`
- **稳定后处理链**：来自 `v8.2`

## 这包解决了什么问题

之前的 `v8.x` 只覆盖 runner / summarize / export / figure / report，不包含真实训练脚本和环境文件，不能单独启动完整实验。本包把：

- `env_141.py`
- `train_gnn_fedgrid.py`
- `evaluate_topology_shift_deterministic.py`
- `fedgrid_federated.py`
- `run_case141_fedgrid_v6.py`
- `summarize_fedgrid_suite_v6.py`
- `export_fedgrid_tables_v6.py`
- `make_fedgrid_figures_v6.py`
- `make_fedgrid_report_v6.py`

放进了同一个根目录里，因此 Claude / Codex / 本地执行都不需要自己拼版本。

## 根目录就是 project_root

你可以直接把当前目录当成 `project_root`：

```bash
cd fedgrid_runtime_bundle_v1
python scripts/check_runtime_bundle.py --project_root .
```

## 最短启动路径

### 1. 预检

```bash
python scripts/check_runtime_bundle.py --project_root .
```

### 2. main dry run

```bash
python run_case141_fedgrid_v6.py \
  --project_root . \
  --suite_name case141_fedgrid_main_rr \
  --preset main \
  --methods preset \
  --seeds 0 1 2 \
  --train_topology_mode random_reset \
  --outage_k 6 \
  --outage_policy local \
  --outage_radius 2 \
  --gpu 0 \
  --epochs 100 \
  --no_post \
  --dry_run
```

### 3. 正式运行

```bash
python run_case141_fedgrid_v6.py \
  --project_root . \
  --suite_name case141_fedgrid_main_rr \
  --preset main \
  --methods preset \
  --seeds 0 1 2 \
  --train_topology_mode random_reset \
  --outage_k 6 \
  --outage_policy local \
  --outage_radius 2 \
  --gpu 0 \
  --epochs 100 \
  --no_post
```

### 4. 后处理

```bash
bash scripts/run_postprocess.sh python outputs/suites/case141_fedgrid_main_rr
```

## 先读哪几份文档

1. `docs/VERSION_MAP_AND_SOURCE_OF_TRUTH.md`
2. `docs/ENVIRONMENT_SETUP_CONDA_AND_UV.md`
3. `docs/EXPERIMENT_RUNBOOK.md`
4. `docs/CLAUDE_CODEX_EXECUTION_GUIDE.md`
5. `docs/RESULTS_CHECKLIST.md`
6. `docs/PAPER_TABLE_MAPPING.md`

For the curated document map, see:

- `docs/README.md`

## Skill

如果你想把这套运行规范上传到 ChatGPT Skills，使用：

- `dist/skill.zip`

如果你想查看 skill 源目录：

- `skills/fedgrid-runtime-runner/`
