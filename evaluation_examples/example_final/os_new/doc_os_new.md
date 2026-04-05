# OS New 任务设计文档

## 0. OS New 验证策略

### 0.1 核心定位

`os_new` 是一组面向 Ubuntu / GNOME 桌面环境的本地系统任务，重点覆盖以下四类能力：

1. **GNOME 系统设置**：时区、屏幕锁定、夜灯、通知、电源、收藏夹、辅助功能等。
2. **文件系统与 Shell 工作流**：复制、移动、重命名、筛选、压缩、权限修改、清单生成等。
3. **终端环境配置**：终端尺寸持久化、默认别名、文本转换、脚本输出核验等。
4. **系统管理与服务编排**：蓝牙、用户切换、SFTP 用户、cron、systemd timer/service、UFW、防火墙规则等。

### 0.2 核心思路

`os_new` 的验证采用统一的两阶段模式：

1. **VM 端数据收集**：通过 `vm_command_line` 在虚拟机内执行确定性 shell 命令，输出结构化的 `key=value` 文本，或者直接输出目标文件内容。
2. **宿主机侧 Python 判定**：评估函数位于 `desktop_env/evaluators/metrics/basic_os.py`，负责解析 collector 输出并依据 `rules` 做最终判定。

**设计原则**：collector 只负责“取证”，不承担 PASS / FAIL 逻辑；全部判定统一放在 Python evaluator 中，便于复用、调试和版本迭代。

### 0.3 评估器通用模式

```python
def check_os_xxx(result: str, rules: dict) -> float:
    """
    参数：
        result: 从 VM 收集到的 key=value 文本，或直接读取到的文件内容
        rules: 期望值字典
    返回：
        1.0（通过）或 0.0（失败）
    """
    try:
        kv = _parse_kv(result)
        # ...逐项校验
        return 1.0
    except Exception:
        return 0.0
```

### 0.4 对应的 JSON evaluator 结构

```json
{
  "evaluator": {
    "func": "check_os_xxx",
    "result": {
      "type": "vm_command_line",
      "command": "echo timezone=$(timedatectl show -p Timezone --value); echo ntp=$(timedatectl show -p NTPSynchronized --value)"
    },
    "expected": {
      "type": "rule",
      "rules": {
        "timezone": "Etc/UTC",
        "ntp": "active"
      }
    }
  }
}
```

### 0.5 与音频 / 图形类任务的区别

| 特性 | OS New | Audacity / Blender 类任务 |
|------|--------|---------------------------|
| 主要产物 | shell 输出、配置状态、文件系统状态 | 导出文件、项目文件、图形产物 |
| result 类型 | `vm_command_line` | 常见为 `vm_file` 或 VM 内脚本执行 |
| 核验方式 | 解析 `key=value` / 文件内容 | 下载产物后本地分析，或在 VM 内跑专用脚本 |
| 依赖 | shell 命令 + Python 标准库 | 取决于目标应用与文件格式 |
| 核心难点 | 状态一致性、幂等性、系统副作用控制 | 产物结构、格式解析、数值容差 |

---

## 1. 可用资源

### 1.1 数据来源方式

`os_new` **不依赖静态素材包**。绝大多数任务通过 `config.execute` 在任务开始前动态构造测试环境，包括：

- 创建目录树和测试文件。
- 写入模板文本、脚本和配置文件。
- 初始化 GNOME `gsettings` 状态。
- 初始化用户、组、服务、定时器或防火墙相关前置状态。

因此 `os_new` 的任务数据具备以下特点：

- **自包含**：单个 JSON 即可完整描述初始化和验证。
- **零外部文件依赖**：无需额外上传素材。
- **可重复 reset**：更适合系统设置和文件操作型 benchmark。

### 1.2 常见 config 初始化模式

| config 类型 | 典型用途 | 说明 |
|-------------|---------|------|
| `execute` + `shell=true` | 创建目录、写测试文件、初始化系统状态 | 最常见的初始化方式 |
| `execute` + Python / pyautogui | 聚焦桌面、打开终端、触发 GUI 操作前置动作 | 仅少量任务使用 |
| evaluator `postconfig` | 在评估前补做一次状态采样或新开终端验证 | 当前主要用于终端尺寸持久化任务 |

### 1.3 当前任务集统计

| 指标 | 值 |
|------|----|
| 任务总数 | **39** |
| L1（基础操作） | **15** |
| L2（复合操作） | **14** |
| L3（高级工作流） | **10** |
| snapshot | 全部为 `os` |
| related_apps | 全部为 `os` |
| result 类型 | 全部为 `vm_command_line` |
| 已使用评估函数数 | **37** |
| `basic_os.py` 中 `check_os_*` 总数 | **38** |
| 环境风险 `low` | **28** |
| 环境风险 `medium` | **9** |
| 环境风险 `high` | **2** |

### 1.4 source 字段策略

当前 `source` 字段已统一改为可追溯的外部参考来源，优先引用 GNOME / Ubuntu 官方帮助、Ubuntu manpage、Canonical 教程或 Freedesktop 规范，采用 `外部参考来源：资料标题 (URL)` 的写法。

- `source` 主要记录与任务操作最接近的公开资料，作为 benchmark 任务设计时的外部参考锚点。
- 如果外部资料只覆盖通用操作范式，而任务还包含 benchmark 特有约束，这些约束仍由 `instruction` 与 evaluator 承担，不额外写入 `source`。
- 这批任务仍是内部 benchmark 组装而成，因此不单独补充 `author`；文档中的 `source` 与 JSON 中的 `source` 保持一一对应。

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/basic_os.py`

### 2.1 内部辅助函数与遗留函数

| 函数名 | 类别 | 描述 |
|--------|------|------|
| `_parse_kv(output)` | 核心辅助 | 将 `key=value` 文本解析为 `dict` |
| `check_gnome_favorite_apps` | 遗留 | 旧版 GNOME 收藏夹检查 |
| `is_utc_0` | 遗留 | 旧版 UTC 时区检查 |
| `check_text_enlarged` | 遗留 | 旧版文本缩放检查 |
| `check_moved_jpgs` | 遗留 | 旧版 JPG 移动检查 |
| `is_in_vm_clickboard` | 遗留 | 旧版剪贴板调试辅助 |

### 2.2 GNOME / 桌面设置评估器

| 函数名 | 描述 | 当前是否使用 |
|--------|------|--------------|
| `check_os_timezone_utc` | 校验时区、NTP、报告文件 | 是 |
| `check_os_gnome_favorites` | 校验收藏夹顺序与审计文件 | 是 |
| `check_os_accessibility` | 校验大字体、光标大小、放大镜 | 是 |
| `check_os_screen_lock` | 校验锁屏开关、空闲延时、锁定延时 | 是 |
| `check_os_night_light` | 校验夜灯开关、色温和状态文件 | 是 |
| `check_os_notifications` | 校验通知横幅和锁屏通知 | 是 |
| `check_os_power_settings` | 校验 dim / idle-delay 等电源设置 | 是 |
| `check_os_battery_config` | 校验电池百分比与电源模式输出 | 是 |
| `check_os_audio_config` | 校验默认输出设备音量与静音状态 | 是 |

### 2.3 文件系统评估器

| 函数名 | 描述 | 当前是否使用 |
|--------|------|--------------|
| `check_os_file_manifest` | 直接比对目标文件完整内容 | 否 |
| `check_os_file_operations` | 通用文件存在性 / 缺失 / 内容检查 | 是 |
| `check_os_file_permissions` | 校验目标文件权限 | 是 |
| `check_os_copy_filter` | 校验带筛选条件的复制 / 移动结果 | 是 |
| `check_os_dir_hierarchy` | 校验仅目录层级复制与 manifest | 是 |
| `check_os_compress_logs` | 校验按条件压缩旧日志结果 | 是 |
| `check_os_deploy_files` | 校验多节点散发部署结果 | 是 |
| `check_os_trash_recovery` | 校验垃圾箱恢复结果 | 是 |
| `check_os_rename_dirs` | 校验目录重命名和 rename log | 是 |
| `check_os_extract_services` | 校验从日志中提取故障服务名 | 是 |
| `check_os_recent_manifest` | 校验最近文本文件 CSV manifest | 是 |
| `check_os_disk_cleanup` | 校验磁盘清理与报告文件 | 是 |
| `check_os_batch_extract` | 校验批量解压与分类整理 | 是 |

### 2.4 Shell / 终端环境评估器

| 函数名 | 描述 | 当前是否使用 |
|--------|------|--------------|
| `check_os_terminal_size` | 校验终端尺寸持久化与 `.bashrc` 备份 | 是 |
| `check_os_python_alias` | 校验 `python` / `pip` 默认别名 | 是 |
| `check_os_php_line_count` | 校验 PHP 递归统计输出 | 是 |
| `check_os_text_transform` | 校验文本转 HTML 列表结果 | 是 |
| `check_os_meeting_template` | 校验模板文件与状态文件 | 是 |

### 2.5 系统管理 / 服务编排评估器

| 函数名 | 描述 | 当前是否使用 |
|--------|------|--------------|
| `check_os_bluetooth_service` | 校验蓝牙服务 enabled / active | 是 |
| `check_os_install_local_app` | 校验本地应用安装、launcher 和 desktop entry | 是 |
| `check_os_switch_user` | 校验切换用户后文件内容与属主 | 是 |
| `check_os_sftp_user` | 校验 SFTP 用户、组、目录和权限 | 是 |
| `check_os_cron_job` | 校验 cron 条目、调度表达式与报告 | 是 |
| `check_os_hosts_block` | 校验 `/etc/hosts` 拦截、备份和报告 | 是 |
| `check_os_systemd_timer_basic` | 校验基础 systemd timer/service | 是 |
| `check_os_quota_dirs` | 校验多用户组目录权限矩阵 | 是 |
| `check_os_log_rotate_pipeline` | 校验日志轮转、压缩、归档和报告 | 是 |
| `check_os_systemd_custom_service` | 校验自定义 service + timer 全生命周期 | 是 |
| `check_os_firewall_rules` | 校验 UFW 规则、默认策略和报告 | 是 |

### 2.6 评估实现汇总

| 指标 | 数值 |
|------|------|
| `check_os_*` 总数 | **38** |
| 当前任务实际使用 | **37** |
| 预留未使用 | **1** |
| 预留函数 | `check_os_file_manifest` |

---

## 3. 任务定义

### 3.1 第一级（L1）—— 基础操作（单步、可直接验证）—— 15 个

L1 任务以单一目标为主，每个任务围绕一个核心系统设置或一个局部文件 / Shell 操作展开。与 Audacity 一样，这一层追求“动作原子化 + 结果可直接验证”，但初始化方式改为 OS 任务特有的动态状态构造。

L1 任务统一采用以下模式：

- **初始化方式**：通过 `config.execute` 动态创建测试文件、重置 `gsettings` 或清理旧报告文件。
- **验证方式**：通过 `vm_command_line` 收集系统状态、文件内容或审计结果。
- **主要考察**：GNOME 桌面设置、基础文件筛选、文本处理、用户级命令环境。

> L1 数据检查结论：现有 15 个任务整体覆盖面已经足够，但原先有少数任务的初始状态不够确定，且 `battery_power_config` 的 evaluator 未完整覆盖 instruction。已补强以下点：
>
> 1. `accessibility_magnifier` 现在会先重置为较小字体 / 光标并关闭放大镜，避免起始态已经满足目标。
> 2. `night_light_status_report` 现在会先关闭夜灯并重置温度。
> 3. `set_timezone_utc` 现在会尝试将时区置为非 UTC 作为初始态，提高任务非平凡性。
> 4. `battery_power_config` 现在不仅检查电池百分比，还校验电源模式为 `balanced` 或 `unsupported`。
> 5. `downloads_collect_pngs_flat` 改为使用专用 `check_os_copy_filter` evaluator，覆盖更明确的筛选型文件操作能力。

---

#### 任务 L1-1：设置时区为 UTC

- **ID**：`b6781586-6346-41cd-935a-a6b1487918fc`
- **task_slug**：`set_timezone_utc`
- **指令**：Set system time zone to UTC (UTC+0), keep automatic time synchronization enabled, and write `~/Desktop/timezone_report.txt` with exactly: `timezone=Etc/UTC` and `ntp=active` on separate lines.
- **source**：外部参考来源：GNOME Help - Change your timezone (https://help.gnome.org/users/gnome-help/stable/clock-timezone.html.en)
- **能力分类**：Time Zone Configuration
- **初始化数据**：清空 `~/Desktop/timezone_report.txt`，并尝试将系统时区置为非 UTC，确保任务不是默认直通。
- **评估函数**：`check_os_timezone_utc`
- **result**：`vm_command_line` → `timedatectl` 当前时区、NTP 状态 + `~/Desktop/timezone_report.txt`
- **expected**：`rule` → `{"timezone": "Etc/UTC", "ntp": "active"}`
- **验证逻辑**：系统时区必须为 `Etc/UTC`，NTP 必须处于 `active`，且报告文件内容完全匹配。
- **需要新评估函数**：❌

---

#### 任务 L1-2：配置 GNOME 收藏夹

- **ID**：`ec4e3f68-9ea4-4c18-a5c9-69f89d1178b3`
- **task_slug**：`gnome_favorites_list`
- **指令**：Set GNOME favorites to exactly three apps in this order: `thunderbird.desktop`, `google-chrome.desktop`, `org.gnome.Terminal.desktop`. Ensure `vim.desktop` is removed. Then write the same ordered list to `~/Desktop/favorites_audit.txt`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Add apps to the favorites bar (https://help.ubuntu.com/lts/ubuntu-help/shell-apps-favorites.html.en)
- **能力分类**：Dock Favorites Management
- **初始化数据**：预设收藏夹中包含 `vim.desktop`，并清空审计文件。
- **评估函数**：`check_os_gnome_favorites`
- **result**：`vm_command_line` → GNOME 收藏夹列表 + `favorites_audit.txt` 是否匹配
- **expected**：`rule` → `{"expected_apps": ["thunderbird.desktop", "google-chrome.desktop", "org.gnome.Terminal.desktop"]}`
- **验证逻辑**：收藏夹应用必须与目标列表完全一致且顺序一致，审计文件同步输出相同顺序。
- **需要新评估函数**：❌

---

#### 任务 L1-3：辅助功能放大与大字体

- **ID**：`3ce045a0-877b-42aa-8d2c-b4a863336ab8`
- **task_slug**：`accessibility_magnifier`
- **指令**：Enable Large Text (`text scaling >= 1.2`), set cursor size to at least `48`, and enable screen magnifier with magnification factor `> 1.5`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Make the text larger (https://help.ubuntu.com/lts/ubuntu-help/a11y-font-size.html.en)；Ubuntu Desktop Guide - Magnify a screen area (https://help.ubuntu.com/lts/ubuntu-help/a11y-mag.html.en)
- **能力分类**：Accessibility Display Tuning
- **初始化数据**：将文字缩放重置到 `1.0`、光标重置到 `24`、关闭屏幕放大镜并把 magnifier factor 设回低值。
- **评估函数**：`check_os_accessibility`
- **result**：`vm_command_line` → `text_scale`、`cursor_size`、`mag_enabled`、`mag_factor`
- **expected**：`rule` → `{"min_text_scale": 1.2, "min_cursor_size": 48, "min_mag_factor": 1.5}`
- **验证逻辑**：三项 accessibility 指标都必须同时达标，避免仅完成其中一项。
- **需要新评估函数**：❌

---

#### 任务 L1-4：配置屏幕锁定

- **ID**：`a4d98375-215b-4a4d-aee9-3d4370fccc41`
- **task_slug**：`screen_lock_config`
- **指令**：Enable auto screen lock, set idle delay to `300` seconds, set lock delay to `0`, and write `~/Desktop/lock_policy.txt`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Automatically lock your screen (https://help.ubuntu.com/lts/ubuntu-help/privacy-screen-lock.html.en)
- **能力分类**：Screen Lock Policy
- **初始化数据**：预先关闭锁屏，将 `idle-delay` 设为 `0`，并把 `lock-delay` 设为非目标值。
- **评估函数**：`check_os_screen_lock`
- **result**：`vm_command_line` → `lock_enabled`、`idle_delay`、`lock_delay` + 报告文件检查
- **expected**：`rule` → `{"lock_enabled": "true", "idle_delay": "300", "lock_delay": "0"}`
- **验证逻辑**：系统锁屏开关、空闲延时、锁定延时与报告文件三者必须一致。
- **需要新评估函数**：❌

---

#### 任务 L1-5：开启夜灯并保存状态

- **ID**：`f1d3f941-75ba-49bf-abd0-4c92163671e5`
- **task_slug**：`night_light_status_report`
- **指令**：Enable Night Light, set the color temperature to `3700`, and create `~/Desktop/night_light_status.txt` with `enabled=true` and `temperature=3700`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Adjust the Night Light color temperature (https://help.ubuntu.com/lts/ubuntu-help/display-night-light.html.en)
- **能力分类**：Night Light Configuration
- **初始化数据**：预先关闭夜灯、将温度设为 `4000`，并清空状态文件。
- **评估函数**：`check_os_night_light`
- **result**：`vm_command_line` → 夜灯开关、色温 + `night_light_status.txt`
- **expected**：`rule` → `{"enabled": "true", "temperature": "3700"}`
- **验证逻辑**：夜灯必须真正开启、色温精确为 `3700`，且状态文件内容完全匹配。
- **需要新评估函数**：❌

---

#### 任务 L1-6：关闭通知

- **ID**：`f9be0997-4b7c-45c5-b05c-4612b44a6118`
- **task_slug**：`disable_notifications`
- **指令**：Disable notification banners and lock-screen notifications, then write `~/Desktop/dnd_status.txt`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Turn off or adjust notifications (https://help.ubuntu.com/lts/ubuntu-help/shell-notifications.html.en)
- **能力分类**：Notification Policy Control
- **初始化数据**：预先打开通知横幅和锁屏通知，并清空 `dnd_status.txt`。
- **评估函数**：`check_os_notifications`
- **result**：`vm_command_line` → `show_banners`、`show_in_lock_screen` + 报告文件检查
- **expected**：`rule` → `{"show_banners": "false", "show_in_lock_screen": "false"}`
- **验证逻辑**：系统通知状态与报告文件必须同时切换到目标值。
- **需要新评估函数**：❌

---

#### 任务 L1-7：关闭空闲变暗

- **ID**：`bedcedc4-4d72-425e-ad62-21960b11fe0d`
- **task_slug**：`power_no_dim`
- **指令**：Turn off dim screen when inactive, disable automatic screen blanking, and save `~/Desktop/power_policy_audit.txt`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Why does my screen go dim after a while? (https://help.ubuntu.com/lts/ubuntu-help/power-whydim.html.en)；Ubuntu Desktop Guide - Set screen blanking time (https://help.ubuntu.com/lts/ubuntu-help/display-blank.html.en)
- **能力分类**：Idle Power Settings
- **初始化数据**：预先开启 `idle-dim`，将 `idle-delay` 设为 `300`，并清空审计文件。
- **评估函数**：`check_os_power_settings`
- **result**：`vm_command_line` → `idle_dim`、`idle_delay` + 报告文件检查
- **expected**：`rule` → `{"idle_dim": "false", "idle_delay": "0"}`
- **验证逻辑**：要求同时关闭 dim 与自动 blank，避免仅调整其中一项。
- **需要新评估函数**：❌

---

#### 任务 L1-8：显示电池百分比并保持平衡电源模式

- **ID**：`fe41f596-a71b-4c2f-9b2f-9dcd40b568c3`
- **task_slug**：`battery_power_config`
- **指令**：Show battery percentage in the top bar and keep power mode `balanced` if available; otherwise record `unsupported`. Save the result to `~/Desktop/power_ui_status.txt`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Show the battery status as a percentage (https://help.ubuntu.com/lts/ubuntu-help/power-percentage.html.en)；Ubuntu Desktop Guide - Choose a power profile (https://help.ubuntu.com/lts/ubuntu-help/power-profile.html.en)
- **能力分类**：Battery Status Display
- **初始化数据**：预先关闭电池百分比显示；如果系统支持 `powerprofilesctl`，则尝试切换到非目标的 `power-saver`。
- **评估函数**：`check_os_battery_config`
- **result**：`vm_command_line` → `show_battery`、`power_profile` + `power_ui_status.txt`
- **expected**：`rule` → `{"show_battery": "true", "allowed_power_profiles": ["balanced", "unsupported"]}`
- **验证逻辑**：不仅要求显示电池百分比，还要求报告中的电源模式与系统实际状态一致，且只能是 `balanced` 或 `unsupported`。
- **需要新评估函数**：❌

---

#### 任务 L1-9：整理财务 CSV 导出

- **ID**：`367a8a96-74bc-4037-baf9-da9ec38d6a85`
- **task_slug**：`organize_flat_finance_exports`
- **指令**：Move only the top-level `.csv` files from `~/Desktop/finance_exports` into `~/Desktop/finance_exports/csv_ready`, leave `.txt` and nested files untouched, then create an alphabetical manifest.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Flat File Filtering
- **初始化数据**：创建 `jan.csv`、`feb.csv`、`readme.txt` 以及嵌套目录中的 `mar.csv`。
- **评估函数**：`check_os_file_operations`
- **result**：`vm_command_line` → 目标文件存在性、保留文件状态、manifest 内容
- **expected**：`rule` → `{"checks": {"jan_ok": "true", "feb_ok": "true", "no_txt": "true", "txt_kept": "true", "nested_kept": "true", "manifest_ok": "true"}}`
- **验证逻辑**：只允许移动顶层 CSV，不能误带 `.txt` 或嵌套文件，并且 manifest 必须按字母序输出。
- **需要新评估函数**：❌

---

#### 任务 L1-10：收集下载目录中的顶层 PNG

- **ID**：`79f9131c-bfbd-4b01-a177-b31fde8c4a63`
- **task_slug**：`downloads_collect_pngs_flat`
- **指令**：Copy only the top-level `.png` files from `~/Downloads/mock_downloads` into `~/Desktop/selected_pngs`. Do not copy non-png files or anything inside subdirectories. Then create `selected_count.txt` with `count=2`.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Shallow PNG Selection
- **初始化数据**：构造顶层 `chart.png`、`logo.png`、`photo.jpg`，以及子目录中的 `deep.png`。
- **评估函数**：`check_os_copy_filter`
- **result**：`vm_command_line` → 目标文件 present / absent 状态 + `selected_count.txt`
- **expected**：`rule` → `{"present": ["chart.png", "logo.png"], "absent": ["photo.jpg", "deep.png"], "extra_checks": {"count_ok": "true"}}`
- **验证逻辑**：顶层 PNG 必须被复制，非 PNG 和子目录 PNG 必须被排除，并且计数文件必须正确。
- **需要新评估函数**：❌

---

#### 任务 L1-11：文本转 HTML 列表

- **ID**：`5ced85fc-fa1a-4217-95fd-0fb530545ce2`
- **task_slug**：`text_to_html_list`
- **指令**：From `input.txt`, ignore comment lines, trim whitespace, HTML-escape special characters, wrap each kept line as `<li>...</li>`, and write `summary.txt` with the line count.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Text Stream Transformation
- **初始化数据**：预置带空行、注释、前后空格和 HTML 特殊字符的 `input.txt`，删除旧的 `output.txt` 与 `summary.txt`，并打开终端。
- **评估函数**：`check_os_text_transform`
- **result**：`vm_command_line` → `output.txt` 与 `summary.txt` 的精确内容比对结果
- **expected**：`rule` → `{}`
- **验证逻辑**：检查点不在 rules 中，而是由 collector 直接精确比对输出文件和摘要文件内容。
- **需要新评估函数**：❌

---

#### 任务 L1-12：从垃圾箱恢复指定文件

- **ID**：`5ea617a3-0e86-4ba6-aab2-dac9aa2e8d57`
- **task_slug**：`recover_from_trash`
- **指令**：Recover only `poster_party_night.webp` and `guest_list.txt` from Trash into `/home/user/Desktop/recovered_party/`, keep `old_note.txt` in Trash, and preserve original content.
- **source**：外部参考来源：Ubuntu Desktop Guide - Recover a file from the Trash (https://help.ubuntu.com/lts/ubuntu-help/files-recover.html.en)
- **能力分类**：Trash Recovery Workflow
- **初始化数据**：先在桌面创建三份文件，再统一送入 Trash，同时创建空的恢复目标目录。
- **评估函数**：`check_os_trash_recovery`
- **result**：`vm_command_line` → 恢复文件存在性、文件内容、未恢复文件是否仍在垃圾箱
- **expected**：`rule` → `{"checks": {"poster_ok": "true", "guest_ok": "true", "no_old": "true", "content1_ok": "true", "content2_ok": "true", "trash_ok": "true"}}`
- **验证逻辑**：必须只恢复指定文件、保持原始内容，并确保 `old_note.txt` 不被误恢复。
- **需要新评估函数**：❌

---

#### 任务 L1-13：重命名待办目录

- **ID**：`e0df059f-28a6-4169-924f-b9623e7184cc`
- **task_slug**：`rename_todo_dirs`
- **指令**：Rename only `todo_list_Jan_1` and `todo_list_Jan_2` to `done_list_*`, do not rename `backlog_list_Jan_3`, and create `rename_log.txt` in alphabetical order.
- **source**：外部参考来源：Ubuntu Desktop Guide - Rename a file or folder (https://help.ubuntu.com/lts/ubuntu-help/files-rename.html.en)
- **能力分类**：Pattern-Based Renaming
- **初始化数据**：创建三类目录：两个 `todo_list_*` 和一个 `backlog_list_*`。
- **评估函数**：`check_os_rename_dirs`
- **result**：`vm_command_line` → 目标目录是否存在、旧目录是否消失、rename log 是否匹配
- **expected**：`rule` → `{"checks": {"done1_ok": "true", "done2_ok": "true", "backlog_ok": "true", "no_todo1": "true", "no_todo2": "true", "log_ok": "true"}}`
- **验证逻辑**：只允许重命名指定前缀和指定对象，不能误改 backlog 目录，并且日志必须准确记录映射关系。
- **需要新评估函数**：❌

---

#### 任务 L1-14：创建会议模板

- **ID**：`dac177c7-2dff-4ec9-94b1-a30ea2d11ea6`
- **task_slug**：`create_meeting_template`
- **指令**：Create `~/Templates/meeting_minutes.txt` containing exactly three fixed lines, and create `~/Desktop/template_status.txt` containing `template=meeting_minutes.txt`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Create a document template (https://help.ubuntu.com/lts/ubuntu-help/files-templates.html.en)
- **能力分类**：Template Provisioning
- **初始化数据**：确保 `~/Templates` 存在，并删除旧模板文件与状态文件。
- **评估函数**：`check_os_meeting_template`
- **result**：`vm_command_line` → 模板文件内容与状态文件内容的精确匹配结果
- **expected**：`rule` → `{}`
- **验证逻辑**：模板内容必须逐行完全一致，状态文件必须准确标记模板名称。
- **需要新评估函数**：❌

---

#### 任务 L1-15：设置 `python` / `pip` 默认别名

- **ID**：`c288e301-e626-4b98-a1ab-159dcb162af5`
- **task_slug**：`python_pip_alias`
- **指令**：Set user-level defaults so that `python` runs Python 3 and `pip` points to `pip3`, without removing system binaries. Then write `~/Desktop/python_default_report.txt`.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Shell Alias Setup
- **初始化数据**：删除 `~/.local/bin/python`、`~/.local/bin/pip` 和旧报告文件，并确保 `~/.local/bin` 存在。
- **评估函数**：`check_os_python_alias`
- **result**：`vm_command_line` → `python` / `pip` 解析结果 + 报告文件检查
- **expected**：`rule` → `{}`
- **验证逻辑**：要求用户级默认命令解析到 Python 3 / pip3，且报告文件与系统行为一致。
- **需要新评估函数**：❌

---

### L1 任务汇总

| # | 任务名称 | task_slug | 评估函数 | 风险 |
|---|----------|-----------|----------|------|
| 1 | 设置时区为 UTC | `set_timezone_utc` | `check_os_timezone_utc` | `medium` |
| 2 | 配置 GNOME 收藏夹 | `gnome_favorites_list` | `check_os_gnome_favorites` | `low` |
| 3 | 辅助功能放大与大字体 | `accessibility_magnifier` | `check_os_accessibility` | `low` |
| 4 | 配置屏幕锁定 | `screen_lock_config` | `check_os_screen_lock` | `low` |
| 5 | 开启夜灯并保存状态 | `night_light_status_report` | `check_os_night_light` | `low` |
| 6 | 关闭通知 | `disable_notifications` | `check_os_notifications` | `low` |
| 7 | 关闭空闲变暗 | `power_no_dim` | `check_os_power_settings` | `low` |
| 8 | 显示电池百分比并保持平衡电源模式 | `battery_power_config` | `check_os_battery_config` | `medium` |
| 9 | 整理财务 CSV 导出 | `organize_flat_finance_exports` | `check_os_file_operations` | `low` |
| 10 | 收集下载目录中的顶层 PNG | `downloads_collect_pngs_flat` | `check_os_copy_filter` | `low` |
| 11 | 文本转 HTML 列表 | `text_to_html_list` | `check_os_text_transform` | `low` |
| 12 | 从垃圾箱恢复指定文件 | `recover_from_trash` | `check_os_trash_recovery` | `low` |
| 13 | 重命名待办目录 | `rename_todo_dirs` | `check_os_rename_dirs` | `low` |
| 14 | 创建会议模板 | `create_meeting_template` | `check_os_meeting_template` | `low` |
| 15 | 设置 `python` / `pip` 默认别名 | `python_pip_alias` | `check_os_python_alias` | `low` |

**L1 统计**：

- 总任务数：**15**
- 使用的评估函数：**15** 个
- 风险分布：`low` 13 个，`medium` 2 个，`high` 0 个
- 能力覆盖：GNOME / 电源 / 辅助功能设置 8 个，文件与目录操作 4 个，Shell / 文本与用户级环境 3 个

#### L1 覆盖评审

从覆盖面看，L1 已经不只是“点一个开关”的轻任务，而是覆盖了：

1. **桌面可访问性与使用偏好**：时区、收藏夹、锁屏、夜灯、通知、电源、电池、辅助功能。
2. **基础文件筛选与整理**：平铺目录复制 / 移动、垃圾箱恢复、定向重命名。
3. **轻量 Shell / 终端能力**：文本转换、模板写入、用户级命令别名设置。

保留 L1 的同时，已通过初始化和验证补强，避免任务退化成默认环境即可通过的“伪简单题”。

### 3.2 第二级（L2）—— 复合操作（2-4 个关联动作）—— 14 个

L2 任务要求智能体把多个相关步骤串起来完成，重点考察“理解约束 + 组织命令 / GUI 操作 + 生成可审计结果”的能力。相对 L1，L2 的关键不只是把某个状态调对，而是要同时满足筛选条件、输出格式、持久化要求或系统副作用控制。

L2 任务统一采用以下模式：

- **初始化方式**：通过 `config.execute` 构造更复杂的目录树、服务初始态、权限矩阵或脚本素材。
- **验证方式**：仍以 `vm_command_line` 为主，但 collector 往往同时检查状态、文件内容和副产物。
- **主要考察**：终端环境持久化、批处理文件工作流、服务管理、用户 / 会话切换、系统级配置落地。

> L2 复查结论：现有 14 个任务的能力覆盖已经较丰富，`func` 也是 14 个任务对应 14 个 evaluator，整体同质化不高。本轮主要做的是“合理性和可验证性修正”，而不是重做题库：
>
> 1. `audio_config_volume` 现在会先尝试把默认 sink 调低并设为静音，避免默认环境直接接近目标态。
> 2. `terminal_size_persist` 现在会先从 `.bashrc` 中移除目标 `stty` 行，并删除旧备份文件，确保需要真实完成持久化设置。
> 3. `php_line_count` 去掉了原先“还要打印到终端”的未验证要求，只保留可稳定核验的文件输出目标。
> 4. `switch_user_session` 去掉了“必须切回原会话”这类当前 evaluator 无法稳定验证的附加要求。

---

#### 任务 L2-1：配置输出设备音量

- **ID**：`28cc3b7e-b194-4bc9-8353-d04c0f4d56d2`
- **task_slug**：`audio_config_volume`
- **指令**：Configure the default output sink so that volume is exactly `100%`, mute is off, and save the active sink name into `/home/user/Desktop/audio_status/active_sink.txt`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Change the sound volume (https://help.ubuntu.com/lts/ubuntu-help/sound-volume.html.en)；Ubuntu Desktop Guide - If you hear no sound or low volume (https://help.ubuntu.com/lts/ubuntu-help/sound-nosound.html.en)
- **能力分类**：Audio Sink Configuration
- **初始化数据**：创建 `audio_status` 目录并删除旧 sink 文件；若系统存在默认 sink，则尝试将其音量预设为较低值并置为静音。
- **评估函数**：`check_os_audio_config`
- **result**：`vm_command_line` → `volume`、`mute`、`sink_file_ok`
- **expected**：`rule` → `{"volume": "100", "mute": "no"}`
- **验证逻辑**：默认输出设备必须精确为 100% 音量、解除静音，并把当前 active sink 名称正确写入文件。
- **复合动作数**：3（找到默认输出设备 → 调整音量与静音 → 写入 sink 文件）
- **需要新评估函数**：❌

---

#### 任务 L2-2：终端尺寸持久化

- **ID**：`13584542-872b-42d8-b299-866967b5c3ef`
- **task_slug**：`terminal_size_persist`
- **指令**：Configure terminal size to be persistent with `140` columns and `46` rows. Also create a backup of `~/.bashrc` as `~/.bashrc.osworld.bak`. The setting must take effect in a newly opened terminal automatically.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Persistent Terminal Profile
- **初始化数据**：备份当前 `.bashrc` 到 seed 文件；移除已有的目标 `stty rows 46 cols 140` 行，并清除旧的 `.bashrc.osworld.bak`。
- **评估函数**：`check_os_terminal_size`
- **result**：`vm_command_line` → `backup_ok`、`bashrc_ok`、`size_ok`
- **expected**：`rule` → `{"rows": "46", "cols": "140"}`
- **验证逻辑**：必须创建 `.bashrc` 备份；目标 `stty` 行在 `.bashrc` 中恰好出现一次；在 evaluator `postconfig` 新开终端后，尺寸自动生效为 `46 140`。
- **复合动作数**：3（备份 `.bashrc` → 写入持久化配置 → 在新终端中生效）
- **需要新评估函数**：❌

---

#### 任务 L2-3：递归统计 PHP 行数

- **ID**：`4127319a-8b79-4410-b58a-7a151e15f3d7`
- **task_slug**：`php_line_count`
- **指令**：Count total lines from all `.php` files under `/home/user/project_hard`, excluding any path under `vendor/` and any file ending with `.test.php`, then save the exact result as `TOTAL=<number>` into `/home/user/project_hard/php_line_total.txt`.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Recursive Code Metrics
- **初始化数据**：构造 `src/`、`vendor/`、`tests/`、`module/sub/` 目录，并放入多份 PHP 文件，其中包含应排除的 `vendor` 文件和 `.test.php` 文件。
- **评估函数**：`check_os_php_line_count`
- **result**：`vm_command_line` → `file_exists`、`content_ok`
- **expected**：`rule` → `{"expected_total": "TOTAL=9"}`
- **验证逻辑**：只统计符合条件的 `.php` 文件行数，输出文件必须存在且内容精确为 `TOTAL=9`。
- **复合动作数**：2（筛选符合条件的 PHP 文件 → 统计并写结果）
- **需要新评估函数**：❌

---

#### 任务 L2-4：递归设置日志权限

- **ID**：`4d117223-a354-47fb-8b45-62ab1390a95f`
- **task_slug**：`set_log_perms`
- **指令**：Recursively set permission `640` for all regular `.log` files under `~/Desktop/perm_lab`, but do not change anything under `archive/`, do not modify non-`.log` files, and keep directory permissions unchanged.
- **source**：外部参考来源：Ubuntu manpage - chmod(1) (https://manpages.ubuntu.com/manpages/jammy/en/man1/chmod.1.html)
- **能力分类**：Selective Permission Hardening
- **初始化数据**：构造多级目录树，放入普通 `.log`、隐藏目录中的 `.log`、`archive/old.log`、`readme.txt`、`run.sh`，并预设不同权限值。
- **评估函数**：`check_os_file_permissions`
- **result**：`vm_command_line` → 各目标文件权限键值对
- **expected**：`rule` → `{"permissions": {"serviceA_app": "640", "serviceB_error": "640", "hidden": "640", "archive_old": "755", "readme": "666", "run": "700"}}`
- **验证逻辑**：只有非 `archive/` 下的普通 `.log` 需要被统一改成 `640`；`archive` 中的 `.log` 与非 `.log` 文件权限必须保持原值。
- **复合动作数**：3（递归筛选目标 `.log` → 排除 archive → 精确修改权限）
- **需要新评估函数**：❌

---

#### 任务 L2-5：复制失败 Notebook 并保留层级

- **ID**：`5c1075ca-bb34-46a3-a7a0-029bd7463e79`
- **task_slug**：`copy_failed_notebooks`
- **指令**：Copy all files matching `*failed.ipynb` into `./fails` while preserving directory hierarchy, exclude any file under a `tmp` directory and any file whose basename starts with `draft_`, then create `fails_manifest.txt` containing sorted sha256 + relative path entries.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Hierarchical File Collection
- **初始化数据**：创建多个项目目录，包含应复制的 `model_failed.ipynb`、`eval_failed.ipynb`，也包含 `tmp/` 下文件、`draft_` 文件以及无关 `.ipynb` / `.txt` 文件。
- **评估函数**：`check_os_file_operations`
- **result**：`vm_command_line` → 是否复制目标文件、是否排除禁拷文件、manifest 是否正确
- **expected**：`rule` → `{"checks": {"model_ok": "true", "eval_ok": "true", "no_cache": "true", "no_secret": "true", "no_draft": "true", "manifest_ok": "true"}}`
- **验证逻辑**：要同时满足模式匹配、层级保留、路径排除和 manifest 排序哈希输出四项要求。
- **复合动作数**：4（筛选 failed notebook → 排除 tmp / draft_ → 保留层级复制 → 生成 manifest）
- **需要新评估函数**：❌

---

#### 任务 L2-6：本地安装 Spotify 启动器

- **ID**：`94d95f96-9699-4208-98ba-3c3119edf9c2`
- **task_slug**：`install_spotify_local`
- **指令**：Install the provided local Spotify script into `~/.local/opt/spotify/spotify`, create an executable launcher at `~/.local/bin/spotify`, add a desktop entry at `~/.local/share/applications/spotify.desktop`, and ensure `spotify --version` prints `Spotify mock 2.0.0`.
- **source**：外部参考来源：Freedesktop.org - XDG Base Directory Specification (https://specifications.freedesktop.org/basedir-spec/latest/)；Freedesktop.org - Desktop Entry Specification (https://specifications.freedesktop.org/desktop-entry-spec/latest/)
- **能力分类**：Local App Installation
- **初始化数据**：预置本地 installer payload 脚本，清空旧的目标目录、launcher 与 desktop entry。
- **评估函数**：`check_os_install_local_app`
- **result**：`vm_command_line` → `binary_ok`、`launcher_ok`、`desktop_ok`、`version_ok`
- **expected**：`rule` → `{}`
- **验证逻辑**：本地安装必须完整落地到二进制、启动器、桌面入口三处，并且命令行版本输出准确。
- **复合动作数**：4（复制 payload → 创建 launcher → 写 desktop entry → 验证版本）
- **需要新评估函数**：❌

---

#### 任务 L2-7：切换到 `charles` 用户会话并写确认文件

- **ID**：`a462a795-fdc7-4b23-b689-e8b6df786b78`
- **task_slug**：`switch_user_session`
- **指令**：Switch to user `charles` without logging out, and as `charles` create `/tmp/charles_session_ok.txt` containing exactly `whoami=charles` and `home=/home/charles` on separate lines.
- **source**：外部参考来源：Ubuntu Desktop Guide - Log out, power off or switch users (https://help.ubuntu.com/lts/ubuntu-help/shell-exit.html.en)
- **能力分类**：User Session Handover
- **初始化数据**：若 `charles` 不存在则创建该用户并设置密码，清理旧的 `/tmp/charles_session_ok.txt`。
- **评估函数**：`check_os_switch_user`
- **result**：`vm_command_line` → `file_exists`、`content_ok`、`owner_ok`
- **expected**：`rule` → `{}`
- **验证逻辑**：目标文件必须由 `charles` 创建，内容精确匹配，文件属主也必须是 `charles`。
- **复合动作数**：2（切换用户 → 以目标用户身份写文件）
- **需要新评估函数**：❌

---

#### 任务 L2-8：提取故障服务列表

- **ID**：`d1a9c9e6-62b7-4fb1-b48f-4f6c90c9b5e1`
- **task_slug**：`extract_failing_services`
- **指令**：Collect all unique service names whose log lines contain level `ERROR` or `CRITICAL` and status `>=500`, ignore anything under `archive/`, and save the sorted names to `~/Desktop/log_audit/report/failing_services.txt`.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Log Incident Extraction
- **初始化数据**：创建多份日志文件，其中包含应保留的 `auth`、`billing`、`cache`、`payments`，也包含应排除的 `404`、`INFO` 和 `archive/` 中旧日志。
- **评估函数**：`check_os_extract_services`
- **result**：`vm_command_line` → 目标报告文件内容直接读取
- **expected**：`rule` → `{"expected": "auth\nbilling\ncache\npayments"}`
- **验证逻辑**：需要同时完成日志过滤、阈值筛选、去重、排序和目标路径输出。
- **复合动作数**：4（筛选日志行 → 过滤 archive/ 与低状态码 → 去重排序 → 写报告）
- **需要新评估函数**：❌

---

#### 任务 L2-9：配置定时清理 cron

- **ID**：`a7c1d2e3-4f56-4a89-b012-3c4d5e6f7a8b`
- **task_slug**：`setup_cron_cleanup`
- **指令**：Create a user cron job that runs every day at `2:30 AM` to delete `.tmp` files in `/tmp` older than `7` days, using the exact `find /tmp -name '*.tmp' -mtime +7 -delete` command, and create `~/Desktop/cron_setup_report.txt`.
- **source**：外部参考来源：Ubuntu manpage - crontab(5) (https://manpages.ubuntu.com/manpages/jammy/en/man5/crontab.5.html)
- **能力分类**：Cron Automation Setup
- **初始化数据**：清空用户 crontab 并删除旧报告文件，同时打开终端。
- **评估函数**：`check_os_cron_job`
- **result**：`vm_command_line` → `cron_exists`、`schedule_ok`、`command_ok`、`output_ok`
- **expected**：`rule` → `{"checks": {"cron_exists": "true", "schedule_ok": "true", "command_ok": "true", "output_ok": "true"}}`
- **验证逻辑**：既要求 cron 条目存在，也要求调度表达式、命令内容和报告文件全部严格匹配。
- **复合动作数**：3（写 crontab → 保持命令精确匹配 → 写审计报告）
- **需要新评估函数**：❌

---

#### 任务 L2-10：批量解压并分类

- **ID**：`c9e3f4a5-6b78-4cad-d234-5e6f7a8b9c0d`
- **task_slug**：`batch_extract_classify`
- **指令**：Extract all `.tar.gz` and `.zip` files from `~/Desktop/archives_inbox` into `~/Desktop/extracted/`, then move `.csv` files into `data/`, `.txt` files into `docs/`, `.sh` files into `scripts/`, and create `summary.txt` with counts.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Archive Extraction Pipeline
- **初始化数据**：生成一个 `.tar.gz` 和一个 `.zip`，其中包含 `.csv`、`.txt`、`.sh` 三类文件各两份。
- **评估函数**：`check_os_batch_extract`
- **result**：`vm_command_line` → 分类后的目标文件存在性 + `summary_ok`
- **expected**：`rule` → `{"checks": {"csv1": "true", "csv2": "true", "txt1": "true", "txt2": "true", "sh1": "true", "sh2": "true", "summary_ok": "true"}}`
- **验证逻辑**：要求先正确解压，再按扩展名重组输出目录，并写出正确的分类计数摘要。
- **复合动作数**：4（批量解压 → 分类移动 `.csv` → 分类移动 `.txt` / `.sh` → 写 summary）
- **需要新评估函数**：❌

---

#### 任务 L2-11：清理磁盘缓存并生成报告

- **ID**：`b8d2e3f4-5a67-4b9c-c123-4d5e6f7a8b9c`
- **task_slug**：`disk_cleanup_report`
- **指令**：Delete all `.log` files larger than `1KB` and all empty directories in `~/Desktop/project_cache`, keep `.conf` and `.dat` files untouched, and create `~/Desktop/cleanup_report.txt` with deletion / keep counts.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Disk Cleanup Audit
- **初始化数据**：构造两个大 `.log`、一个小 `.log`、保留类 `.conf` / `.dat` 文件以及多个空目录。
- **评估函数**：`check_os_disk_cleanup`
- **result**：`vm_command_line` → 目标大日志是否删除、小日志 / 配置文件是否保留、空目录是否清除、报告是否正确
- **expected**：`rule` → `{"checks": {"big_gone": "true", "huge_gone": "true", "small_kept": "true", "conf_kept": "true", "dat_kept": "true", "empty1_gone": "true", "emptysub_gone": "true", "report_ok": "true"}}`
- **验证逻辑**：大小阈值、扩展名过滤、空目录检测和报告统计四类约束必须同时满足。
- **复合动作数**：4（按大小删除日志 → 删除空目录 → 保留配置文件 → 写清理报告）
- **需要新评估函数**：❌

---

#### 任务 L2-12：创建基础 systemd timer

- **ID**：`e1a5b6c7-8d90-4ecf-f456-7a8b9c0d1e2f`
- **task_slug**：`systemd_timer_basic`
- **指令**：Create `/usr/local/bin/hourly_cleanup.sh`, create `hourly-cleanup.service` and `hourly-cleanup.timer` with `OnCalendar=hourly`, enable and start the timer, and write `~/Desktop/timer_status.txt`.
- **source**：外部参考来源：Ubuntu manpage - systemctl(1) (https://manpages.ubuntu.com/manpages/jammy/en/man1/systemctl.1.html)；Ubuntu manpage - systemd.timer(5) (https://manpages.ubuntu.com/manpages/jammy/en/man5/systemd.timer.5.html)
- **能力分类**：Basic Timer Automation
- **初始化数据**：停用并删除旧 timer / service / script / 日志，`daemon-reload` 后清空状态文件。
- **评估函数**：`check_os_systemd_timer_basic`
- **result**：`vm_command_line` → `service_file_ok`、`timer_file_ok`、`timer_enabled`、`timer_active`、`script_ok`、`report_ok`
- **expected**：`rule` → `{"checks": {"service_file_ok": "true", "timer_file_ok": "true", "timer_enabled": "true", "timer_active": "true", "script_ok": "true", "report_ok": "true"}}`
- **验证逻辑**：脚本、service、timer 三个层面都必须正确落地，且 timer 必须已 enabled + active，并同步输出状态报告。
- **复合动作数**：4（写脚本 → 写 service → 写 timer → enable + start 并写报告）
- **需要新评估函数**：❌

---

#### 任务 L2-13：屏蔽恶意域名

- **ID**：`d0f4a5b6-7c89-4dbe-e345-6f7a8b9c0d1e`
- **task_slug**：`hosts_block_domains`
- **指令**：Add `127.0.0.1` entries for `ads.example.com`, `tracker.example.net`, and `malware.badsite.org` to `/etc/hosts`, create a backup at `/etc/hosts.bak`, keep existing hosts entries, and write `~/Desktop/hosts_block_report.txt`.
- **source**：外部参考来源：Ubuntu manpage - hosts(5) (https://manpages.ubuntu.com/manpages/jammy/en/man5/hosts.5.html)
- **能力分类**：Host-Based Domain Blocking
- **初始化数据**：备份原始 `/etc/hosts` 为内部基线副本，移除可能已有的目标域名拦截条目，删除旧的 `/etc/hosts.bak` 和报告文件。
- **评估函数**：`check_os_hosts_block`
- **result**：`vm_command_line` → `blocked_ads`、`blocked_tracker`、`blocked_malware`、`preserved_ok`、`backup_ok`、`report_ok`
- **expected**：`rule` → `{"checks": {"blocked_ads": "true", "blocked_tracker": "true", "blocked_malware": "true", "preserved_ok": "true", "backup_ok": "true", "report_ok": "true"}}`
- **验证逻辑**：三个域名必须全部被拦截，同时原 hosts 内容需被保留，并且必须生成系统级备份和用户侧报告。
- **复合动作数**：3（备份 hosts → 追加拦截条目 → 写报告并保留原条目）
- **需要新评估函数**：❌

---

#### 任务 L2-14：启用蓝牙服务

- **ID**：`b3d4a89c-53f2-4d6b-8b6a-541fb5d205fa`
- **task_slug**：`enable_bluetooth`
- **指令**：Enable the `bluetooth` systemd service, make it persistent across reboot, and create `~/Desktop/bluetooth_status.txt` with `enabled=yes` and `active=yes`.
- **source**：外部参考来源：Ubuntu Desktop Guide - Turn Bluetooth on or off (https://help.ubuntu.com/lts/ubuntu-help/bluetooth-turn-on-off.html.en)
- **能力分类**：Bluetooth Service Enablement
- **初始化数据**：若需要则尝试安装 `bluez`，并显式 `disable` + `stop` 现有 bluetooth 服务，同时删除旧状态文件。
- **评估函数**：`check_os_bluetooth_service`
- **result**：`vm_command_line` → `enabled`、`active`、`file_ok`
- **expected**：`rule` → `{"enabled": "enabled", "active": "active"}`
- **验证逻辑**：要求 bluetooth 服务当前处于 active 状态，并且 systemd 层面被 enable，状态文件内容也必须匹配。
- **复合动作数**：3（启用服务 → 启动服务 → 写状态文件）
- **需要新评估函数**：❌

---

### L2 任务汇总

| # | 任务名称 | task_slug | 评估函数 | 风险 |
|---|----------|-----------|----------|------|
| 1 | 配置输出设备音量 | `audio_config_volume` | `check_os_audio_config` | `low` |
| 2 | 终端尺寸持久化 | `terminal_size_persist` | `check_os_terminal_size` | `low` |
| 3 | 递归统计 PHP 行数 | `php_line_count` | `check_os_php_line_count` | `low` |
| 4 | 递归设置日志权限 | `set_log_perms` | `check_os_file_permissions` | `low` |
| 5 | 复制失败 Notebook 并保留层级 | `copy_failed_notebooks` | `check_os_file_operations` | `low` |
| 6 | 本地安装 Spotify 启动器 | `install_spotify_local` | `check_os_install_local_app` | `low` |
| 7 | 切换到 `charles` 用户会话并写确认文件 | `switch_user_session` | `check_os_switch_user` | `medium` |
| 8 | 提取故障服务列表 | `extract_failing_services` | `check_os_extract_services` | `low` |
| 9 | 配置定时清理 cron | `setup_cron_cleanup` | `check_os_cron_job` | `low` |
| 10 | 批量解压并分类 | `batch_extract_classify` | `check_os_batch_extract` | `low` |
| 11 | 清理磁盘缓存并生成报告 | `disk_cleanup_report` | `check_os_disk_cleanup` | `low` |
| 12 | 创建基础 systemd timer | `systemd_timer_basic` | `check_os_systemd_timer_basic` | `medium` |
| 13 | 屏蔽恶意域名 | `hosts_block_domains` | `check_os_hosts_block` | `medium` |
| 14 | 启用蓝牙服务 | `enable_bluetooth` | `check_os_bluetooth_service` | `high` |

**L2 统计**：

- 总任务数：**14**
- 使用的评估函数：**14** 个
- 风险分布：`low` 10 个，`medium` 3 个，`high` 1 个
- 能力覆盖：终端与用户级环境 4 个，文件 / 批处理工作流 5 个，系统服务与定时任务 4 个，用户 / 会话切换 1 个

#### L2 覆盖评审

从覆盖结构看，L2 已经明显区别于 L1：

1. **终端与用户级环境**：音频 sink、终端持久化、PHP 统计、本地应用安装，要求配置落地并生成审计文件。
2. **批处理文件工作流**：failed notebook 拷贝、批量解压、日志权限、磁盘清理，强调筛选规则和产物一致性。
3. **系统管理能力**：cron、systemd timer、bluetooth、`/etc/hosts`，涉及持久化系统配置与副作用控制。
4. **会话 / 身份切换**：`switch_user_session` 补上了用户上下文切换这一类能力，不再只是文件处理题。

因此 L2 整体能力面已经足够丰富；本轮修改主要是提升起始态确定性并去除无法稳定验证的附加要求，而不是增加新题。

### 3.3 第三级（L3）—— 高级工作流（10 个）

L3 任务包含更多跨目录、跨用户或跨系统组件的组合操作，强调完整工作流和系统副作用控制。

#### 任务 L3-1：递归收集 JPG 并生成哈希清单

- **ID**：`23393935-50c7-4a86-aeea-2b78fd089c5c`
- **task_slug**：`collect_jpg_manifest`
- **指令**：In `~/Desktop/photos_hard`, recursively collect only `.jpg` files into `~/Desktop/cpjpg_hard` while preserving directory hierarchy. Exclude any file under a `private` directory and any filename containing `_raw`. Then create `~/Desktop/cpjpg_hard/manifest.txt` containing sha256 and relative path for copied jpgs only, sorted by relative path.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Recursive Asset Collection
- **初始化数据**：构造 `trip/a`、`trip/private`、`family`、`events/sub` 多级目录；其中包含应复制的 `sun.jpg`、`night.jpg`，以及应排除的 `portrait_raw.jpg`、`private/secret.jpg` 和无关 `us.png`。
- **评估函数**：`check_os_file_operations`
- **result**：`vm_command_line` → 两个目标 JPG 是否复制、`_raw` / `private` 是否被排除、manifest 内容是否与复制结果匹配。
- **expected**：`rule` → `{"checks": {"sun_ok": "true", "night_ok": "true", "no_raw": "true", "no_private": "true", "manifest_ok": "true"}}`
- **验证逻辑**：要求同时满足扩展名筛选、目录排除、文件名排除、层级保留和 sha256 清单输出五项约束。
- **复合动作数**：4（筛选 `.jpg` → 排除 `private` / `_raw` → 保留层级复制 → 生成并排序 manifest）
- **需要新评估函数**：❌

---

#### 任务 L3-2：压缩旧日志并输出压缩报告

- **ID**：`37887e8c-da15-4192-923c-08fa390a176d`
- **task_slug**：`compress_old_logs`
- **指令**：In `/tmp/test_files_hard`, compress only `.log` and `.txt` files that were modified at least `30` days ago into `.gz` files in place. Exclude anything under `archive/`. Keep newer files unchanged. Then create `/tmp/test_files_hard/compress_report.txt` listing each compressed file relative path (without `.gz`), sorted alphabetically.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Conditional Log Compression
- **初始化数据**：生成旧的 `error.log`、`report.txt`、旧的 `data.csv`、`archive/old/ignore.log`，以及较新的 `recent.log`；通过 `touch -d` 显式制造时间差。
- **评估函数**：`check_os_compress_logs`
- **result**：`vm_command_line` → 旧 `.log` / `.txt` 是否被压缩、较新日志是否保留、`csv` 与 `archive/` 是否未误压缩、压缩报告是否正确。
- **expected**：`rule` → `{"checks": {"error_gz": "true", "report_gz": "true", "no_recent": "true", "recent_kept": "true", "no_csv_gz": "true", "no_archive_gz": "true", "report_ok": "true"}}`
- **验证逻辑**：该任务不是单纯 `gzip`，而是同时要求时间筛选、扩展名筛选、路径排除和报告产出。
- **复合动作数**：4（按时间筛选旧文件 → 过滤类型 → 排除 `archive/` → 原地压缩并写报告）
- **需要新评估函数**：❌

---

#### 任务 L3-3：仅复制目录层级并生成目录清单

- **ID**：`4783cc41-c03c-4e1b-89b4-50658f642bd5`
- **task_slug**：`copy_dir_hierarchy`
- **指令**：Copy only the directory hierarchy from `/home/user/Desktop/source_tree` to `/home/user/Desktop/target_tree_hard` recursively. Exclude any directory named `tmp` or `.git` and exclude any path under `cache/`. Do not copy any regular files. After finishing, create `/home/user/Desktop/target_tree_hard/manifest_dirs.txt` containing all copied relative directory paths, one per line, sorted alphabetically.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Directory Skeleton Replication
- **初始化数据**：构造 `projectA/src`、`projectA/tmp/a`、`projectA/.git/hooks`、`projectB/docs/api`、`projectB/cache/x`、`projectC/empty/sub` 等目录，并插入多个普通文件以防“直接整棵复制”误过。
- **评估函数**：`check_os_dir_hierarchy`
- **result**：`vm_command_line` → 目标目录是否完整保留、`tmp` / `.git` / `cache` 是否排除、普通文件是否未被复制、目录 manifest 是否完全匹配。
- **expected**：`rule` → `{"checks": {"projectA_src": "true", "projectB_api": "true", "projectC_sub": "true", "no_tmp": "true", "no_git": "true", "no_cache": "true", "no_files": "true"}, "manifest_match": "true"}`
- **验证逻辑**：要求智能体区分“目录存在”与“文件复制”两个层面，避免用粗暴复制后再删除文件的方式留下遗漏。
- **复合动作数**：4（遍历目录树 → 排除禁拷目录 → 只重建目录结构 → 生成目录清单）
- **需要新评估函数**：❌

---

#### 任务 L3-4：配置 SFTP-only 用户与 SSH 限制

- **ID**：`5812b315-e7bd-4265-b51f-863c02174c28`
- **task_slug**：`create_sftp_user`
- **指令**：Create an SFTP-only user named `charles` with password `Ex@mpleP@55w0rd!`, home directory `/home/test1`, shell `/usr/sbin/nologin`, and primary group `sftpusers`. Set `/home/test1` ownership to `root:root` with permission `755`, then create `/home/test1/upload` owned by `charles:sftpusers` with permission `750`. Also create `/etc/ssh/sshd_config.d/charles-sftp.conf` so members of `sftpusers` are forced to use `internal-sftp` with `ChrootDirectory /home/test1`, `AllowTcpForwarding no`, and `X11Forwarding no`.
- **source**：外部参考来源：Ubuntu manpage - useradd(8) (https://manpages.ubuntu.com/manpages/jammy/en/man8/useradd.8.html)；Ubuntu manpage - usermod(8) (https://manpages.ubuntu.com/manpages/jammy/en/man8/usermod.8.html)；OpenSSH manual - sshd_config(5) (https://man7.org/linux/man-pages/man5/sshd_config.5.html)
- **能力分类**：SFTP Access Provisioning
- **初始化数据**：删除既有 `charles` 用户、`sftpusers` 组、旧 `/home/test1` 目录以及历史 `charles-sftp.conf`，确保任务必须完整重建用户、目录和 SSH 限制配置。
- **评估函数**：`check_os_sftp_user`
- **result**：`vm_command_line` → 组存在、用户存在、home 路径、nologin shell、primary group、`/home/test1` 权限、`upload/` 权限，以及 SSH drop-in 配置是否正确。
- **expected**：`rule` → `{"checks": {"group_ok": "true", "user_ok": "true", "home_ok": "true", "shell_ok": "true", "primary_group_ok": "true", "home_perm_ok": "true", "upload_perm_ok": "true", "ssh_conf_ok": "true"}}`
- **验证逻辑**：本轮已将该题从“纯用户创建”加固为“用户 + chroot 目录 + sshd drop-in 限制”三段式系统配置任务，更符合 L3。
- **复合动作数**：5（创建组 → 创建用户并设主组 / shell → 配置 chroot 目录权限 → 创建 upload 目录 → 写 SSH SFTP 限制）
- **需要新评估函数**：❌

---

#### 任务 L3-5：递归向 node* 目录部署文件

- **ID**：`6f56bf42-85b8-4fbb-8e06-6c44960184ba`
- **task_slug**：`deploy_to_nodes`
- **指令**：In `~/Desktop/deploy_lab/clusters`, recursively find every directory whose basename matches `node*` and copy `source/file1` into each of them, excluding any path containing `/backup/`. Keep the copied file name as `file1`, preserve the source file modification time, and set copied file permission to `600`.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Recursive Node Deployment
- **初始化数据**：构造 `node1`、`node2/sub/node2a`、`group/node3`、`backup/node4`、`node5/backup/deep` 等路径，并设置源文件固定修改时间，制造“递归 basename 匹配 + 备份路径排除 + 元数据保留”的组合约束。
- **评估函数**：`check_os_deploy_files`
- **result**：`vm_command_line` → `node1`、`node2a`、`node3` 是否正确部署且内容、权限、mtime 一致；`backup/node4` 与 `node5/backup/deep` 是否保持未部署。
- **expected**：`rule` → `{"checks": {"node1_ok": "true", "node2a_ok": "true", "node3_ok": "true", "no_backup_node4": "true", "no_backup_deep": "true"}}`
- **验证逻辑**：这类题容易被“只扫第一层”或“按路径片段误匹配”做错，因此显式要求递归查找 basename 为 `node*` 的目录。
- **复合动作数**：4（递归匹配目标目录 → 排除 `/backup/` 路径 → 批量复制 → 保留 mtime 并设权限）
- **需要新评估函数**：❌

---

#### 任务 L3-6：配置完整 UFW 防火墙策略

- **ID**：`c5e9f0a1-2b34-4acd-d890-1e2f3a4b5c6d`
- **task_slug**：`firewall_rules`
- **指令**：Configure a complete firewall policy using UFW (Uncomplicated Firewall). Reset UFW, set default incoming to deny and outgoing to allow, allow `22/tcp`、`80/tcp`、`443/tcp`, deny `3306/tcp`, add a source-based allow rule for subnet `10.0.0.0/24`, enable logging at `medium`, and create `/etc/ufw/firewall_report.txt` with the exact summary lines.
- **source**：外部参考来源：Ubuntu manpage - ufw(8) (https://manpages.ubuntu.com/manpages/jammy/en/man8/ufw.8.html)
- **能力分类**：Firewall Policy Orchestration
- **初始化数据**：执行 `ufw --force reset`、禁用现有 UFW，并删除旧报告文件，确保不是在已有策略上增量叠加。
- **评估函数**：`check_os_firewall_rules`
- **result**：`vm_command_line` → UFW 是否 active、SSH/HTTP/HTTPS 是否 allow、MySQL 是否 deny、子网规则是否存在、默认策略、logging 级别以及报告文件精确内容。
- **expected**：`rule` → `{"checks": {"ufw_active": "true", "ssh_ok": "true", "http_ok": "true", "https_ok": "true", "mysql_deny": "true", "subnet_ok": "true", "default_deny": "true", "default_allow_out": "true", "logging_ok": "true", "report_ok": "true"}}`
- **验证逻辑**：本轮修正了原始任务里“报告要求包含 `subnet_10=allowed`，但 evaluator 未检查”的问题；现在 collector 会验证完整报告内容。
- **复合动作数**：6（reset UFW → 设默认策略 → 配置端口规则 → 配置子网规则 → 打开 logging → 写精确报告）
- **需要新评估函数**：❌

---

#### 任务 L3-7：构建日志轮转脚本流水线

- **ID**：`a3c7d8e9-0f12-4eab-b678-9c0d1e2f3a4b`
- **task_slug**：`log_rotate_pipeline`
- **指令**：Build a log rotation pipeline for application logs in `/var/log/myapp/`: create initial logs, write `/usr/local/bin/rotate_logs.sh`, rotate each `.log` to `.log.1.gz`, recreate empty `644` logs, move archives into `/var/log/myapp/archive/`, run the script once, and write `rotation_report.txt` with `rotated_count=3`.
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Log Rotation Pipeline
- **初始化数据**：清理旧的 `/var/log/myapp` 和已有 `rotate_logs.sh`，要求从空状态完成目录、脚本和首次轮转。
- **评估函数**：`check_os_log_rotate_pipeline`
- **result**：`vm_command_line` → 脚本是否存在且可执行、archive 目录权限、三份 `.gz` 是否归档完成、三份新日志是否为空且权限为 `644`、报告文件是否正确。
- **expected**：`rule` → `{"checks": {"script_ok": "true", "archive_dir_ok": "true", "app_gz": "true", "error_gz": "true", "access_gz": "true", "fresh_app": "true", "fresh_error": "true", "fresh_access": "true", "report_ok": "true"}}`
- **验证逻辑**：同时覆盖脚本编写、日志轮转、压缩、归档、权限恢复和首次执行验证，是典型多阶段系统流水线题。
- **复合动作数**：6（创建日志目录与样本 → 写脚本 → 创建 archive → 执行轮转 → 生成新日志 → 写报告）
- **需要新评估函数**：❌

---

#### 任务 L3-8：配置多用户 setgid 项目空间

- **ID**：`f2b6c7d8-9e01-4fda-a567-8b9c0d1e2f3a`
- **task_slug**：`multi_user_quota_dirs`
- **指令**：Set up a shared project workspace for three teams: create group `projectx`, create users `alice`、`bob`、`charlie`, add them to the group, create `/srv/projectx/` as `root:projectx` with `2775`, create `team_alpha/`、`team_beta/`、`team_gamma/`, and enforce differentiated owners / permissions, then create `README.txt`.
- **source**：外部参考来源：Ubuntu manpage - useradd(8) (https://manpages.ubuntu.com/manpages/jammy/en/man8/useradd.8.html)；Ubuntu manpage - usermod(8) (https://manpages.ubuntu.com/manpages/jammy/en/man8/usermod.8.html)；Ubuntu manpage - chmod(1) (https://manpages.ubuntu.com/manpages/jammy/en/man1/chmod.1.html)
- **能力分类**：Shared Permission Architecture
- **初始化数据**：删除既有三名用户、`projectx` 组和 `/srv/projectx`，避免任务退化为“局部修补现成配置”。
- **评估函数**：`check_os_quota_dirs`
- **result**：`vm_command_line` → 组存在、三名用户是否在组内、根目录 setgid 权限、三个子目录属主 / 属组 / 权限矩阵，以及 README 内容。
- **expected**：`rule` → `{"checks": {"group_ok": "true", "alice_ok": "true", "bob_ok": "true", "charlie_ok": "true", "root_dir_ok": "true", "alpha_ok": "true", "beta_ok": "true", "gamma_ok": "true", "readme_ok": "true"}}`
- **验证逻辑**：该题关注多用户权限矩阵与 setgid 共享目录语义，而不只是“能否 mkdir 成功”。
- **复合动作数**：5（创建组 → 创建用户并入组 → 创建 setgid 根目录 → 创建三类子目录并分别授权 → 写 README）
- **需要新评估函数**：❌

---

#### 任务 L3-9：生成最近文本文件统计 CSV

- **ID**：`f2b7a4c1-98dd-41d5-b0d1-2a0f6f53c8de`
- **task_slug**：`recent_txt_manifest`
- **指令**：In `~/Desktop/release_bundle`, create `~/Desktop/release_bundle/output/recent_txt_manifest.csv` with every `.txt` file modified within the last `10` days, excluding any file under a `tmp` directory. Each line must be formatted as `relative_path,line_count` and sorted by `line_count` (descending), then `relative_path` (ascending).
- **source**：外部参考来源：Canonical tutorial - Command line for beginners (https://ubuntu.com/tutorials/command-line-for-beginners)
- **能力分类**：Recent Text Inventory
- **初始化数据**：构造 `docs/`、`notes/`、`module/x/`、`module/tmp/`、`old/` 等目录，放入多份 `.txt` 与一个无关 `.md`，并通过 `touch -d` 显式区分“最近 2 天”和“20 天前”的文件。
- **评估函数**：`check_os_recent_manifest`
- **result**：`vm_command_line` → 直接输出 `recent_txt_manifest.csv` 的文件内容。
- **expected**：`rule` → `{"expected": "module/x/info.txt,5\ndocs/a.txt,3\nnotes/c.txt,3\ndocs/b.txt,1"}`
- **验证逻辑**：该任务组合了时间过滤、路径排除、逐文件行数统计、双关键字排序和 CSV 格式化，虽然不涉及高权限，但流程长度足以达到 L3。
- **复合动作数**：5（筛选近 10 天 `.txt` → 排除 `tmp/` → 统计行数 → 排序 → 写 CSV）
- **需要新评估函数**：❌

---

#### 任务 L3-10：创建自定义 healthcheck service 与 timer

- **ID**：`b4d8e9f0-1a23-4fbc-c789-0d1e2f3a4b5c`
- **task_slug**：`systemd_custom_service`
- **指令**：Create a complete custom systemd service that runs a health-check script on a timer: write `/usr/local/bin/healthcheck.sh`, create `healthcheck.service` and `healthcheck.timer`, reload daemon, enable and start the timer, manually run the service once to produce a log entry, and create `/etc/healthcheck.conf`.
- **source**：外部参考来源：Ubuntu manpage - systemctl(1) (https://manpages.ubuntu.com/manpages/jammy/en/man1/systemctl.1.html)；Ubuntu manpage - systemd.service(5) (https://manpages.ubuntu.com/manpages/jammy/en/man5/systemd.service.5.html)；Ubuntu manpage - systemd.timer(5) (https://manpages.ubuntu.com/manpages/jammy/en/man5/systemd.timer.5.html)
- **能力分类**：Custom Service Scheduling
- **初始化数据**：停止并禁用旧 timer，删除旧 service / timer / script / log / config 文件，然后 `daemon-reload`，确保必须从空白 systemd 状态重建。
- **评估函数**：`check_os_systemd_custom_service`
- **result**：`vm_command_line` → 脚本可执行性、service 配置、timer 配置、timer active / enabled 状态、日志输出以及 `/etc/healthcheck.conf` 内容。
- **expected**：`rule` → `{"checks": {"script_ok": "true", "svc_ok": "true", "timer_ok": "true", "timer_active": "true", "timer_enabled": "true", "log_ok": "true", "conf_ok": "true"}}`
- **验证逻辑**：要求同时完成脚本、service、timer、首次执行日志和配置文件五个层面，且其中多个环节依赖 `systemctl` 生命周期管理。
- **复合动作数**：6（写脚本 → 写 service → 写 timer → daemon-reload → enable + start → 手动执行并写配置）
- **需要新评估函数**：❌

---

### L3 任务汇总

| # | 任务名称 | task_slug | 评估函数 | 风险 |
|---|----------|-----------|----------|------|
| 1 | 递归收集 JPG 并生成哈希清单 | `collect_jpg_manifest` | `check_os_file_operations` | `low` |
| 2 | 压缩旧日志并输出压缩报告 | `compress_old_logs` | `check_os_compress_logs` | `low` |
| 3 | 仅复制目录层级并生成目录清单 | `copy_dir_hierarchy` | `check_os_dir_hierarchy` | `low` |
| 4 | 配置 SFTP-only 用户与 SSH 限制 | `create_sftp_user` | `check_os_sftp_user` | `medium` |
| 5 | 递归向 node* 目录部署文件 | `deploy_to_nodes` | `check_os_deploy_files` | `low` |
| 6 | 配置完整 UFW 防火墙策略 | `firewall_rules` | `check_os_firewall_rules` | `high` |
| 7 | 构建日志轮转脚本流水线 | `log_rotate_pipeline` | `check_os_log_rotate_pipeline` | `medium` |
| 8 | 配置多用户 setgid 项目空间 | `multi_user_quota_dirs` | `check_os_quota_dirs` | `medium` |
| 9 | 生成最近文本文件统计 CSV | `recent_txt_manifest` | `check_os_recent_manifest` | `low` |
| 10 | 创建自定义 healthcheck service 与 timer | `systemd_custom_service` | `check_os_systemd_custom_service` | `medium` |

#### L3 统计

- 总任务数：**10**
- 主要覆盖：复杂文件工作流、用户与权限矩阵、systemd / UFW 级系统配置。
- 风险分布：`low` 5 个，`medium` 4 个，`high` 1 个。
- 使用的评估函数：**10** 个，当前 L3 任务均为一任务一函数。

#### L3 覆盖评审

本轮对 L3 的复查重点不是“再堆几个高权限任务”，而是确保每道题都真正体现出高级工作流的组合性。结论如下：

1. **系统级配置题已经足够形成 L3 核心**：`firewall_rules`、`systemd_custom_service`、`log_rotate_pipeline`、`multi_user_quota_dirs` 原本就具备较强的跨组件依赖；其中 `firewall_rules` 现已修复报告校验遗漏，`systemd_custom_service` 和 `log_rotate_pipeline` 保持为完整生命周期题。
2. **`create_sftp_user` 已做实质性加固**：原版本更像“用户 + 权限”题，偏向 L2；现在新增 `sshd_config.d` drop-in 约束，要求把账户、chroot 目录和 SFTP 强制策略连成一套配置，难度与层次更符合 L3。
3. **文件工作流虽然占比不低，但并不重复**：`collect_jpg_manifest` 强调层级复制与哈希清单，`compress_old_logs` 强调时间条件与原地压缩，`copy_dir_hierarchy` 强调“只复制目录”，`deploy_to_nodes` 强调递归目标发现与元数据保留，`recent_txt_manifest` 强调筛选 + 统计 + 排序 + CSV 输出。五题约束轴线不同，没有简单同质化成“换一批文件名再做一次”。
4. **保留了低风险 L3 题的必要性**：L3 不等于全部高权限。像 `recent_txt_manifest` 这类题虽然风险低，但其多阶段筛选、计数与排序流程仍然比 L2 更长、更容易出错，因此仍可保留在 L3 作为高级 shell workflow 题。

因此，L3 当前无需新增题目；通过本轮加固与文档细化后，整体已经能较清楚地区分于 L2。

### 3.4 Interactive 任务（interactive_xt）

本节对应目录 `evaluation_examples/examples/interactive_xt` 中的 OS 可交互任务，目标不是替代前面的静态 `os_new` 主集，而是补充一组 **多轮需求演进 / 用户改口 / 中途打断 / 主动澄清** 的桌面系统任务参考。

#### 3.4.1 数据集概览

- **任务数**：15 个
- **任务入口**：全部使用 `"interactive": true`
- **快照**：全部为 `os`
- **风险与网络**：全部为 `proxy=false`、`possibility_of_env_change=low`
- **场景原型**：5 类交互 archetype，每类 3 个任务
- **phase 结构**：2 个任务为 2 phase，11 个任务为 3 phase，2 个任务为 4 phase
- **结果采集**：15 / 15 全部使用 `vm_command_line`
- **最终判定函数**：`exact_match` 11 个，`check_include_exclude` 4 个

| 交互 archetype | 数量 | 代表任务 | 典型触发方式 |
|---|---:|---|---|
| ambiguous_instruction | 3 | `interactive_os_ambiguous_101` | `agent_asks` + `agent_done` |
| requirement_change | 3 | `interactive_os_requirement_change_107` | `agent_done` |
| progressive_refinement | 3 | `interactive_os_progressive_108` | `agent_done` |
| interruption | 3 | `interactive_os_interruption_109` | `step_count` + `agent_done` |
| correction | 3 | `interactive_os_correction_110` | `agent_done` |

从能力覆盖上看，这 15 个任务可以再分成两簇：

1. **文件系统 / 桌面整理工作流**：10 个。主要考察目录创建、文件移动、重命名、筛选、汇总与 manifest 生成。
2. **GNOME 桌面设置工作流**：5 个。主要覆盖收藏栏、电量显示、Night Light、无障碍与锁屏 / 空闲策略。

#### 3.4.2 质量评估

**总体结论**：当前 `interactive_xt` 的 OS 子集在本轮修正后处于 **中上水平**，已经可以作为低风险、可复现的多轮桌面系统交互基线；它的优势是验证稳定、状态闭环清晰，但覆盖面仍然更偏向“本地文件整理 + GNOME 用户级设置”，还没有扩展到更高权限的系统管理交互空间。

**主要优点**：

1. **可验证性强**：15 个任务全部落在文件系统状态或 `gsettings` 状态上，避免了必须依赖视觉截图判断的收尾条件。
2. **交互 archetype 覆盖完整**：模糊、改口、渐进细化、打断、纠错五类模式都具备，且 `agent_asks`、`agent_done`、`step_count` 三类核心触发器都已实际落地。
3. **低环境波动**：全部任务都不依赖外网，且 `possibility_of_env_change` 统一为 `low`，适合作为 interactive pipeline 的稳定基线集。
4. **用户反馈是真正改变执行方向**：不是把一句长 instruction 拆成几段，而是明确要求 Agent 撤销旧目标、调整目录规则、修正 GNOME 设置或重新生成最终报告。

**主要问题 / 剩余风险**：

1. **`step_count` 中断任务仍然是最脆弱的一类**：`interactive_os_interruption_104`、`109`、`115` 仍依赖执行中途插入 follow-up，这比纯 `agent_done` 切换更依赖 Agent 的动作粒度。
2. **能力空间仍偏向用户级桌面任务**：当前没有把 `os_new` 中更强的 systemd、UFW、SFTP、cron 等高权限工作流改造成 interactive 版本，因此还不能代表完整 OS 交互难度。
3. **GNOME 绑定明显**：收藏栏、电量显示、Night Light、无障碍和锁屏题都默认运行在 GNOME 会话内；这与 `snapshot=os` 的当前事实是一致的，但不具备跨桌面环境可移植性。

#### 3.4.3 本轮修正

本轮对 6 个 OS interactive 任务做了针对性加固，重点是让“初始态确定性”与“最终判定稳健性”对齐：

| 任务 | 原问题 | 修正 |
|---|---|---|
| `interactive_os_progressive_103` | 初始无障碍状态未显式重置，可能出现 snapshot 默认态已部分满足目标 | 新增 `text-scaling-factor`、`cursor-size`、`screen-magnifier-enabled`、`mag-factor` 的非目标初始态重置 |
| `interactive_os_progressive_103` | 原版本没有复用已有 OS accessibility 标准评估器，写法不够统一 | 改为对齐 `check_os_accessibility` 的 collector + rule 结构，和 `os_new` 主集保持一致 |
| `interactive_os_progressive_108` | Night Light 温度判定依赖 `uint323700` 这类格式耦合写法 | 改为统一提取数字部分，再校验 `3700` |
| `interactive_os_progressive_113` | `idle-delay` / `lock-delay` 判定依赖 `uint320` 这种 GNOME 输出拼接结果 | 改为统一抽取整数值，再校验 `0` |
| `interactive_os_ambiguous_111`、`interactive_os_correction_114` | GNOME 收藏栏读写未显式声明会话总线环境，和 `os_new` 稳定写法不一致 | 在 setup 和 evaluator 两侧统一补充 `DBUS_SESSION_BUS_ADDRESS` |
| `interactive_os_requirement_change_112` | Phase 1 的“出问题的 service”表述过宽，和 Phase 2 的收紧标准边界不够清楚 | 改成先粗略汇总 `current` 目录里出现过的 service 名称，后续再由用户明确过滤规则 |

修正后，这批任务和静态 `os_new` 主集在两个关键设计点上已经更一致：

1. **涉及 GNOME 设置的题尽量显式重置到非目标态**，避免任务天然直通。
2. **涉及 `gsettings` 数值的题尽量抽取纯数字再比较**，不要把 evaluator 绑定到某一种字符串展示格式。

#### 3.4.4 参考模式

当前这 15 个任务里，以下几题最适合作为后续 OS interactive 扩题参考模板：

1. `interactive_os_requirement_change_107`：目录重命名、文件迁移、目标拆分三者串联，最终状态闭环清楚。
2. `interactive_os_correction_110`：先整体归档，再纠正图片类别，最后叠加重命名，适合做典型 correction 模板。
3. `interactive_os_progressive_108`：跨 `gsettings` 与桌面文件输出，适合作为“系统设置 + 确认文件”型 progressive 模板。
4. `interactive_os_interruption_109`：虽然仍带有 `step_count` 风险，但其“原规则失效、图片改移出项目目录、旧目录必须清理”的结构很适合作为 interruption 设计原型。

#### 3.4.5 后续扩展建议

后续如果继续扩展 OS interactive 子集，优先建议沿下面几个方向补题：

1. **把高权限 OS 题 interactive 化**：例如 firewall、systemd timer、SFTP 用户、cron 规则，在中途插入改口或新增安全约束。
2. **加强收尾显式约束**：当用户说“不要旧目录 / 不要旧文件 / 不要旧设置”时，尽量把“旧目标缺失”写进 `exclude` 或 `exact_match` 判定，而不是只验证新目标存在。
3. **减少对字符串格式偶然性的依赖**：`gsettings` 返回的 `uint32`、布尔值、数组值都应该优先抽取语义值，再做比较。
4. **谨慎使用 `step_count`**：只有确实需要“执行中途被打断”的任务才用它；如果需求变化本质上发生在上一阶段完成之后，优先改为 `agent_done`。
5. **继续保持本地可复现输入**：文件素材、日志样本、目录树和初始设置都应通过 `config.execute` 动态构造，避免把 interactive 任务做成依赖外部环境的脆弱脚本题。

---

## 4. 评估函数汇总

### 4.1 当前任务实际使用的 37 个评估函数

| 类别 | 函数数 | 代表函数 |
|------|--------|----------|
| GNOME / 桌面设置 | 9 | `check_os_timezone_utc`, `check_os_accessibility`, `check_os_audio_config` |
| 文件系统 | 11 | `check_os_file_operations`, `check_os_dir_hierarchy`, `check_os_log_rotate_pipeline` |
| Shell / 终端环境 | 5 | `check_os_terminal_size`, `check_os_text_transform`, `check_os_php_line_count` |
| 系统管理 / 服务 | 11 | `check_os_bluetooth_service`, `check_os_sftp_user`, `check_os_firewall_rules` |

### 4.2 预留但尚未使用的函数

| 函数名 | 预期用途 |
|--------|----------|
| `check_os_file_manifest` | 适合需要直接比较完整文本文件内容的任务 |

---

## 5. Task JSON 模板

### 5.1 单指标 OS 任务模板

```json
{
  "id": "<uuid4>",
  "task_slug": "<task_slug>",
  "difficulty": "L1",
  "snapshot": "os",
  "instruction": "<自然语言任务描述>",
  "source": "外部参考来源：<资料标题> (<URL>)",
  "trajectory": "trajectories/",
  "config": [
    {
      "type": "execute",
      "parameters": {
        "command": "<初始化 shell 命令>",
        "shell": true
      }
    }
  ],
  "related_apps": ["os"],
  "evaluator": {
    "func": "check_os_xxx",
    "result": {
      "type": "vm_command_line",
      "command": "<collector 命令>",
      "shell": true
    },
    "expected": {
      "type": "rule",
      "rules": {
        "checks": {
          "key1": "true",
          "key2": "true"
        }
      }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 5.2 需要 postconfig 的模板

```json
{
  "evaluator": {
    "postconfig": [
      {
        "type": "sleep",
        "parameters": {
          "seconds": 1
        }
      },
      {
        "type": "execute",
        "parameters": {
          "command": [
            "python",
            "-c",
            "<pyautogui 或其他采样动作>"
          ]
        }
      }
    ],
    "func": "check_os_terminal_size",
    "result": {
      "type": "vm_command_line",
      "command": "<collector 命令>",
      "shell": true
    },
    "expected": {
      "type": "rule",
      "rules": {
        "rows": "46",
        "cols": "140"
      }
    }
  }
}
```

---

## 6. 镜像与环境要求

评测镜像至少需要满足以下条件：

1. **Ubuntu / GNOME 桌面环境**，支持 `gsettings`、GNOME Terminal、Files / Trash 等基础桌面能力。
2. **systemd 可用**，支持创建和启用 service / timer。
3. **cron 可用**，支持用户 crontab 配置。
4. **UFW 可用**，支持 reset / allow / deny / logging 等命令。
5. **基础 shell 工具齐全**，包括 `find`、`grep`、`awk`、`sort`、`sha256sum`、`tar`、`zip` / `unzip`、`gzip`。
6. **用户 / 组管理能力可用**，支持 `useradd`、`groupadd`、`usermod` 等操作。
7. **任务执行账号具备所需权限**，否则无法完成 `/etc`、`/usr/local/bin`、`/srv`、`/var/log`、防火墙和 systemd 相关任务。

---

## 7. 任务难度分布总结

| 级别 | 数量 | 描述 | 典型任务 |
|------|------|------|----------|
| L1 | 15 | 单点系统设置或局部文件操作 | 时区、夜灯、通知、模板、垃圾箱恢复 |
| L2 | 14 | 2-4 个步骤的复合操作 | cron、蓝牙、应用安装、日志提取、批量解压 |
| L3 | 10 | 跨目录 / 跨用户 / 跨系统组件工作流 | SFTP 用户、UFW、防火墙、systemd 服务、日志轮转 |
| 总计 | 39 | 以 `vm_command_line` 为核心验证模式 | 全部 `snapshot=os` |

### 可验证性保证

`os_new` 的验证不依赖截图、OCR 或视觉比对，而是依赖以下两类稳定信号：

1. **结构化 shell 输出**：通过 collector 将系统状态转换为稳定的 `key=value` 证据。
2. **确定性文件内容比对**：manifest、report、配置片段等文本文件按精确内容比对。

这使得 OS 任务更适合做高精度、低歧义的程序化评测。

---

## 8. 常见陷阱

### 8.1 collector 输出不稳定

- 不要在 collector 中混入提示语、颜色控制字符或多余空格。
- 尽量输出固定 key 顺序，便于调试和复现。

### 8.2 将判定逻辑写进 shell

- shell 应只做取证，不要把“是否通过”的逻辑提前折叠成单个 PASS / FAIL。
- 复杂判断应放在 `basic_os.py`，避免 collector 失去可解释性。

### 8.3 文件内容比较未排序

- manifest / report 类任务应先排序再写入，避免目录遍历顺序导致非确定性失败。
- 哈希清单建议统一使用 `<sha256>  <relative_path>` 格式。

### 8.4 systemd / cron 任务遗漏收尾步骤

- systemd 任务通常需要 `daemon-reload`、`enable`、`start`，有时还要手动执行一次 service 以生成日志。
- cron 任务应同时验证调度表达式、命令内容和辅助报告文件。

### 8.5 高权限任务副作用过大

- `/etc/hosts`、UFW、用户组管理、SFTP 目录权限等任务必须明确保留哪些既有状态、哪些允许覆盖。
- 这类任务更容易引发环境漂移，文档和 evaluator 都应写清楚约束。

### 8.6 终端持久化类任务验证不足

- 修改 `.bashrc` 或 profile 后，仅检查文件内容不够。
- 应像 `terminal_size_persist` 一样，在 evaluator `postconfig` 中新开终端再次采样。
