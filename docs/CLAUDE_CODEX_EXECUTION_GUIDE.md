# 给 Claude / Codex 的执行指南

## 角色定位

你不是来随便跑命令的，而是来充当**严格执行的本地实验代理**。

你的目标：

1. 先核对 workspace 完整性
2. 按 preset 启动实验
3. 不擅自改 runner / summarize / export / figure / report
4. 报错时先查环境、路径和依赖，再决定是否需要用户确认修改源码
5. 最终交付完整 suite 目录、日志、表、图和简短结论

## 强制约束

### 1. project_root 就是当前统一包根目录

不要再创建“外部 project_root + 外部 handoff bundle”的双根结构。

### 2. 先做预检

```bash
python scripts/check_runtime_bundle.py --project_root .
```

### 3. 先做 dry run

每个新 preset 第一次都先：

```bash
python run_case141_fedgrid_v6.py ... --no_post --dry_run
```

### 4. 默认使用 `--no_post`

训练/评测完成后，再显式运行：

```bash
bash scripts/run_postprocess.sh python <suite_root>
```

### 5. 不要绕过 fail-fast

如果 summarize / figure / report 因数据完整性或多 context 报错，不要继续编造结论。

## 推荐执行顺序

### 第一轮：主结果
1. 预检
2. `main --dry_run`
3. `main`
4. 后处理
5. 检查主表与主图

### 第二轮：消融
1. `ablation`
2. 后处理
3. 对照主结果叙述

### 第三轮：鲁棒性
1. `robustness`
2. 后处理
3. 检查 dropout / byzantine 是否都进 paired 表

## 最小汇报格式

```markdown
# FedGrid local execution update

## Run status
- preset:
- suite_name:
- project_root:
- suite_root:
- completed stages:

## Files produced
- manifests:
- agg:
- reports:

## Checks
- workspace preflight:
- summary/per-episode completeness:
- paired metrics generated:
- figures generated:
- latex tables generated:

## Blocking issues
- [none / list]

## Next action
- [what should be run next]
```
