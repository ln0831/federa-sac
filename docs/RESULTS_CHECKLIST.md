# 结果检查清单

## 一、运行级检查

### 1. manifest 是否完整

应至少包含：

- `fedgrid_v6_run_matrix.csv`
- `fedgrid_v6_commands.csv`
- `fedgrid_v6_suite_manifest.json`
- `fedgrid_v6_postprocess.sh`

### 2. checkpoint 是否齐全

`fedgrid_v6_run_matrix.csv` 里：

- `ckpt_status_post` 应尽量是 `ready`
- `ckpt_bytes` 不应为 0

## 二、评测级检查

### 3. 每个 compare label 是否都有 eval 目录

检查：

```text
outputs/suites/<suite_name>/eval/<compare_label>_seed<seed>/
```

### 4. 每个 eval 目录里是否同时存在

- `summary_*.csv`
- `per_episode_*.csv`

如果只有 summary 没有 per_episode，不可接受。

## 三、聚合级检查

### 5. `agg/` 下是否存在以下关键文件

- `suite_absolute_metrics.csv`
- `suite_paired_metrics.csv`
- `suite_rankings.csv`
- `suite_paper_table_main_random_reset.csv`
- `suite_paper_table_appendix_static.csv`

### 6. paired 表是否覆盖核心方法

至少检查：

- `fedgrid_none`
- `fedgrid_topo_proto`
- `fedgrid_v4_cluster_distill`

如果 robustness preset，还要检查：

- `fedgrid_v4_cluster_dropout`
- `fedgrid_v4_cluster_byzantine`

### 7. paired 表是否只在同 context 内比较

重点检查字段：

- `case`
- `outage_k`
- `outage_policy`
- `outage_radius`
- `topology_mode`

## 四、导出级检查

### 8. LaTeX 表是否生成

- `reports/latex/table_main_random_reset.tex`
- `reports/latex/table_appendix_static.tex`
- `reports/latex/table_ablation_random_reset.tex`

### 9. Figure 是否生成

至少检查：

- `reports/figures/random_reset_delta_return.png`
- `reports/figures/random_reset_delta_vviol.png`
- `reports/figures/random_reset_delta_ploss.png`

### 10. Markdown 报告是否存在

- `reports/fedgrid_v6_report.md`
