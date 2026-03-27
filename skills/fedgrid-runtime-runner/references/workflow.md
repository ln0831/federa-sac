# FedGrid 实验执行 Runbook

## 目标

在当前统一包根目录下，本地执行以下 preset：

- `main`
- `ablation`
- `robustness`
- `full`

并最终导出：

- `agg/*.csv`
- `reports/latex/*.tex`
- `reports/figures/*.png`
- `reports/fedgrid_v6_report.md`

## 一、原则

### 1. 根目录就是 project_root

所有命令默认都从统一包根目录执行：

```bash
cd fedgrid_runtime_bundle_v1
```

### 2. 先 dry run，再正式跑

每个新 preset 第一次都先：

- `--dry_run`
- `--no_post`

### 3. 推荐让 runner 和后处理分离

虽然根目录已经有后处理脚本，但仍建议：

- runner 阶段统一加 `--no_post`
- 完成后再显式调用 `scripts/run_postprocess.sh`

### 4. 不要忽略 fail-fast

如果 summarize 报：

- missing summary/per-episode pairing
- duplicate episodes
- episode alignment mismatch
- multi-context figure input

不要强行继续写结论。

## 二、标准命令

### A. main

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

### B. ablation

```bash
python run_case141_fedgrid_v6.py \
  --project_root . \
  --suite_name case141_fedgrid_ablation_rr \
  --preset ablation \
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

### C. robustness

```bash
python run_case141_fedgrid_v6.py \
  --project_root . \
  --suite_name case141_fedgrid_robust_rr \
  --preset robustness \
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

### D. full

```bash
python run_case141_fedgrid_v6.py \
  --project_root . \
  --suite_name case141_fedgrid_full_rr \
  --preset full \
  --methods all \
  --seeds 0 1 2 \
  --train_topology_mode random_reset \
  --outage_k 6 \
  --outage_policy local \
  --outage_radius 2 \
  --gpu 0 \
  --epochs 100 \
  --no_post
```

## 三、最推荐的执行顺序

1. `main --dry_run`
2. `main`
3. `bash scripts/run_postprocess.sh python outputs/suites/case141_fedgrid_main_rr`
4. `ablation`
5. `robustness`
6. 资源允许时再 `full`

## 四、后处理

```bash
bash scripts/run_postprocess.sh python outputs/suites/case141_fedgrid_main_rr
```

## 五、关键输出目录

- `outputs/suites/<suite_name>/manifests/`
- `outputs/suites/<suite_name>/eval/`
- `outputs/suites/<suite_name>/agg/`
- `outputs/suites/<suite_name>/reports/`
