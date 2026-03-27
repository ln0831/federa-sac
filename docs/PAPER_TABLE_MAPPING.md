# 论文主表 / 附表 / 图 与代码输出的映射

## 主表

### 论文正文主表

建议使用：

- `agg/suite_paper_table_main_random_reset.csv`
- `reports/latex/table_main_random_reset.tex`

对应叙事：

- topology-shift robust 主 benchmark
- 主结论优先基于 `random_reset`

## 附表

### static 附表

使用：

- `agg/suite_paper_table_appendix_static.csv`
- `reports/latex/table_appendix_static.tex`

对应叙事：

- 分布内/弱迁移性能
- 作为 sanity check

## 消融表

使用：

- `reports/latex/table_ablation_random_reset.tex`

## 图

### 正文主图建议

- `reports/figures/random_reset_delta_return.png`
- `reports/figures/random_reset_delta_vviol.png`
- `reports/figures/random_reset_delta_ploss.png`

### 图解释规则

- `delta_return`：越大越好
- `delta_vviol`：越小越好
- `delta_ploss`：越小越好

不要把不同 context 的行画进同一张图。

## 报告

### 结果文字摘要

- `reports/fedgrid_v6_report.md`

用途：

- 给 Claude 提炼结果
- 给你自己写 Discussion 打底

但不要原样复制进论文，需要人工收紧。
