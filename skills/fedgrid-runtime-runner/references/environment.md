# 本地环境搭建（conda 主方案，uv 备选）

## 适用范围

这份文档覆盖当前统一运行包：

- 训练
- 评测
- 汇总
- 出表
- 出图
- 出报告
- pytest 回归

## 一、conda 主方案

### 1. 创建环境

```bash
conda create -n fedgrid-runtime python=3.11 -y
conda activate fedgrid-runtime
```

### 2. 先装最小通用依赖

```bash
pip install matplotlib pytest numpy pandas
```

### 3. 再补训练依赖

当前包没有可靠的完整 `requirements.txt`，因此建议 Claude / Codex 先以导入错误为准补齐。高概率需要：

```bash
pip install torch networkx scipy pandapower gymnasium
```

如果脚本里仍然缺库，再继续补。

### 4. 预检

```bash
python scripts/check_runtime_bundle.py --project_root .
```

## 二、uv 备选方案

### 1. 创建虚拟环境

```bash
uv venv .venv
source .venv/bin/activate
```

### 2. 安装最小依赖

```bash
uv pip install matplotlib pytest numpy pandas
```

### 3. 补训练依赖

```bash
uv pip install torch networkx scipy pandapower gymnasium
```

### 4. 预检

```bash
python scripts/check_runtime_bundle.py --project_root .
```

## 三、建议执行顺序

1. 先 `py_compile`
2. 再 `python scripts/check_runtime_bundle.py --project_root .`
3. 再 `pytest -q tests`
4. 再 `--dry_run`
5. 再正式跑 `main`
6. 最后后处理
