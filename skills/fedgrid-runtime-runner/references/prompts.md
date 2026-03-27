# 可直接复制的 Prompt 模板

## 模板 A：让 Claude 做预检 + dry run

```text
你现在是我的本地实验代理。请严格执行，不要擅自替换脚本版本，也不要把当前工程拆成多个 project root。

当前目录本身就是统一的 FedGrid 运行包根目录。
请按以下步骤执行：
1. 运行 python scripts/check_runtime_bundle.py --project_root .
2. 若预检通过，执行 main preset 的 dry run
3. 把 dry run 生成的 train/eval 命令按清单汇总给我
4. 不要启动正式训练，等我确认
```

## 模板 B：让 Codex 正式跑 main

```text
请在当前统一包根目录本地执行 FedGrid main preset，严格遵守：
- 使用 run_case141_fedgrid_v6.py
- 使用 --no_post
- 不修改 runner、summary、report、figure、export 脚本
- 若发现依赖缺失，先报告缺什么，再最小化安装缺失依赖
- 正式运行后，再调用 bash scripts/run_postprocess.sh python <suite_root>
- 最后输出：suite_root、生成文件列表、阻塞错误、下一步建议

参数：
- project_root: .
- suite_name: case141_fedgrid_main_rr
- preset: main
- seeds: 0 1 2
- train_topology_mode: random_reset
- outage_k: 6
- outage_policy: local
- outage_radius: 2
- gpu: 0
- epochs: 100
```

## 模板 C：让 Claude 只做结果审计

```text
请只做结果审计，不要重跑训练。

目标 suite_root: <suite_root>
请依次检查：
1. manifests 是否完整
2. agg 下是否同时存在 absolute / paired / rankings / paper tables
3. reports 下是否存在 markdown / latex / png
4. suite_paired_metrics.csv 是否覆盖预期方法
5. 是否存在 summary/per_episode 缺失、context 混排、图表误读风险

最后按以下格式输出：
- status
- missing files
- suspicious rows or contexts
- can this suite be used for the paper main table?
```
