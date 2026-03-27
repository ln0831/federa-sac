# 终端指令说明（Windows PowerShell 版）

> 适用环境：Windows PowerShell
>
> 说明：以下命令可直接在 `PS C:\...>` 中运行。换行时请使用 PowerShell 的反引号 `` ` ``，并且**反引号后不要再加空格**。

## 1. Baseline：纯 MLP（FMASAC）
### 推荐：单行直接运行
```powershell
python .\train_fmasac.py --case 141 --topology_mode random_reset --outage_k 4 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --topology_seed 0
```

### 可读性更好的多行写法
```powershell
python .\train_fmasac.py --case 141 `
  --topology_mode random_reset `
  --outage_k 4 --outage_policy local --outage_radius 2 `
  --avoid_slack_hops 1 --topology_seed 0
```

## 2. 方案B：全图共享 bus-GNN（推荐）
### 推荐：单行直接运行
```powershell
python .\train_gnn.py --case 141 --bus_gnn_scope global --bus_gnn_use_base_topology --topology_mode random_reset --outage_k 4 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --topology_seed 0
```

### 可读性更好的多行写法
```powershell
python .\train_gnn.py --case 141 `
  --bus_gnn_scope global `
  --bus_gnn_use_base_topology `
  --topology_mode random_reset `
  --outage_k 4 --outage_policy local --outage_radius 2 `
  --avoid_slack_hops 1 --topology_seed 0
```

## 3. 对照：关闭 bus-GNN（只测试 GraphMixer）
### 推荐：单行直接运行
```powershell
python .\train_gnn.py --case 141 --no_bus_gnn --topology_mode random_reset --outage_k 4 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --topology_seed 0
```

### 可读性更好的多行写法
```powershell
python .\train_gnn.py --case 141 --no_bus_gnn `
  --topology_mode random_reset `
  --outage_k 4 --outage_policy local --outage_radius 2 `
  --avoid_slack_hops 1 --topology_seed 0
```

## 4. 对照：回退到原方案（区域子图 bus-GNN）
### 推荐：单行直接运行
```powershell
python .\train_gnn.py --case 141 --bus_gnn_scope local --topology_mode random_reset --outage_k 4 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --topology_seed 0
```

### 可读性更好的多行写法
```powershell
python .\train_gnn.py --case 141 --bus_gnn_scope local `
  --topology_mode random_reset `
  --outage_k 4 --outage_policy local --outage_radius 2 `
  --avoid_slack_hops 1 --topology_seed 0
```

## 5. 常用参数速查
- `--bus_gnn_scope global|local`：`global` = 方案B；`local` = 旧方案
- `--bus_gnn_use_base_topology`：用基准拓扑构建 bus-GNN 邻接（更稳，推荐在 `random_reset` 下使用）
- `--bus_gnn_lr_scale`：bus-GNN 学习率比例（建议 `0.1` 到 `0.3`）
- `--fed_mode topo|fedavg|none`：联邦聚合方式；方案B下 bus-GNN 已共享，建议优先测试 `none` 或默认设置

## 6. 常见报错说明
如果你看到类似下面的错误：
- “一元运算符 `--` 后面缺少表达式”
- “表达式或语句中包含意外的标记 `topology_mode`”

通常就是因为你在 PowerShell 中使用了 Linux/bash 的续行符 `\`。请改用：
- 单行命令，或
- PowerShell 的反引号 `` ` `` 续行

## 7. 其他终端说明
- **PowerShell**：使用本文件里的写法
- **cmd**：建议全部写成一整行，不要用反引号
- **Git Bash / WSL / Linux**：可以使用反斜杠 `\` 续行
