# 版本映射与唯一事实源

## 当前统一包的来源

### 训练与评测底座
- 来源：`fedgrid_refactor_v4`
- 使用文件：
  - `train_gnn_fedgrid.py`
  - `evaluate_topology_shift_deterministic.py`
  - `env_141.py`
  - `fedgrid_federated.py`
  - 其余图网络/环境/工具模块
- 原因：`v8` runner 需要的 cluster / distill 参数在 `v4` 训练脚本中已经支持，而 `v3` 不完整。

### 稳定 runner
- 来源：`v8.1` / `v8.2`
- 事实源：根目录 `run_case141_fedgrid_v6.py`
- 原因：它已经修复了：
  - `--flag / --no_flag` 布尔契约
  - shell-safe quoting
  - `train_only` / `eval_only` 互斥
  - 更稳的 manifest 输出

### 稳定后处理链
- 事实源：
  - `summarize_fedgrid_suite_v6.py`
  - `export_fedgrid_tables_v6.py`
  - `make_fedgrid_figures_v6.py`
  - `make_fedgrid_report_v6.py`
- 来源：`v8.2`
- 原因：继续修复了：
  - summary/per-episode 完整性校验
  - absolute 去重
  - context-aware report
  - multi-context figure fail-fast
  - TeX 转义正确性

## 明确不要怎么做

- 不要再把 `v8.2` 单独当作完整训练工程。
- 不要把 `v3` 当作默认 project root 再硬接 `v8` runner。
- 不要混用不同目录下的同名脚本。
- 不要让 Claude / Codex 自己猜 project root。

## 当前标准事实源

当前统一包里，**根目录本身就是唯一事实源**。

也就是说：

- `project_root = .`
- runner 就是根目录里的 `run_case141_fedgrid_v6.py`
- 后处理就是根目录里的四个 `*_v6.py`
- 预检和后处理辅助在 `scripts/`
