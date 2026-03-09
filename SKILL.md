---
name: osworld-add-task
description: 指导如何在 OSWorld 基准测试框架中自定义添加新的评估任务
---

# OSWorld 自定义任务添加指南

## 指令

本指南提供在 OSWorld 中添加自定义评估任务的完整步骤。

### 步骤 1: 选择任务领域并创建文件

OSWorld 支持以下任务领域：
- `chrome` - Google Chrome 浏览器操作
- `gimp` - GIMP 图像编辑
- `libreoffice_calc` - LibreOffice 电子表格
- `libreoffice_writer` - LibreOffice 文档编辑
- `libreoffice_impress` - LibreOffice 演示文稿
- `vlc` - VLC 媒体播放器
- `vs_code` - Visual Studio Code
- `thunderbird` - Thunderbird 邮件客户端
- `os` - 操作系统级别任务
- `multi_apps` - 多应用协作任务

```bash
cd evaluation_examples/examples/
# 创建新任务文件（使用 UUID 作为文件名）
touch <domain>/<uuid>.json
```

### 步骤 2: 编写任务 JSON 结构

每个任务 JSON 必须包含以下核心字段：

```json
{
  "id": "unique-task-id",
  "snapshot": "snapshot_id",
  "instruction": "natural_language_instruction",
  "source": "website_url",
  "config": [...],
  "trajectory": "trajectories/",
  "related_apps": ["app1", "app2"],
  "evaluator": {...},
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 步骤 3: 配置初始环境 (config)

`config` 数组定义任务开始前的环境设置：

#### 下载文件
```json
{
  "type": "download",
  "parameters": {
    "files": [
      {
        "url": "https://example.com/file.xlsx",
        "path": "/home/user/file.xlsx"
      }
    ]
  }
}
```

#### 启动应用
```json
{
  "type": "launch",
  "parameters": {
    "command": ["google-chrome", "--remote-debugging-port=1337"]
  }
}
```

#### 执行命令
```json
{
  "type": "execute",
  "parameters": {
    "command": ["mkdir", "-p", "/home/user/Documents/"]
  }
}
```

#### 打开文件
```json
{
  "type": "open",
  "parameters": {
    "path": "/home/user/document.docx"
  }
}
```

### 步骤 4: 选择快照 (snapshot)

根据任务需求选择合适的快照：
- `"os"` - 干净桌面
- `"chrome"` - Chrome 浏览器就绪
- `"gimp"` - GIMP 已安装
- `"libreoffice_writer"` - LibreOffice Writer
- `"libreoffice_calc"` - LibreOffice Calc
- `"vlc"` - VLC 媒体播放器
- `"vs_code"` - Visual Studio Code

### 步骤 5: 配置评估器 (evaluator)

评估器定义如何衡量任务成功：

```json
"evaluator": {
  "postconfig": [...],
  "func": "evaluation_function_name",
  "expected": {...},
  "result": {...}
}
```

#### Postconfig 动作
任务完成后执行的操作（如保存文件、重启应用）：

```json
"postconfig": [
  {
    "type": "execute",
    "parameters": {
      "command": ["python", "-c", "import pyautogui; pyautogui.hotkey('ctrl', 's');"]
    }
  },
  {
    "type": "sleep",
    "parameters": {"seconds": 1}
  }
]
```

#### 常用评估函数

**通用函数** (`desktop_env/evaluators/metrics/general.py`):
- `check_include_exclude` - 检查包含/排除模式
- `exact_match` - 精确字符串匹配
- `match_in_list` - 检查是否在期望列表中
- `fuzzy_match` - 模糊字符串匹配
- `diff_text_file` - 文本文件差异比较

**GIMP 函数** (`desktop_env/evaluators/metrics/gimp.py`):
- `check_brightness_decrease_and_structure_sim` - 亮度降低且结构相似
- `check_contrast_increase_and_structure_sim` - 对比度增加且结构相似
- `check_structure_sim` - 结构相似性检查

**LibreOffice 函数**:
- `compare_table` - 电子表格比较
- `compare_docx_files` - Word 文档比较
- `compare_pptx_files` - PowerPoint 比较

**Chrome 函数**:
- `is_expected_tabs` - 期望的浏览器标签页
- `is_expected_bookmarks` - 书签匹配

### 步骤 6: 定义结果和期望

#### 结果类型
```json
// VM 中的文件
"result": {
  "type": "vm_file",
  "path": "/home/user/output.xlsx",
  "dest": "output.xlsx"
}

// 云端参考文件
"expected": {
  "type": "cloud_file",
  "path": "https://huggingface.co/.../gold.xlsx",
  "dest": "gold.xlsx"
}

// 终端输出
"result": {
  "type": "vm_terminal_output"
}

// 浏览器默认搜索引擎
"result": {
  "type": "default_search_engine"
}
```

### 步骤 7: 添加到任务列表

将任务 ID 添加到 `evaluation_examples/test_all.json`:

```json
{
  "your_domain": [
    "existing-task-id-1",
    "your-new-task-id"
  ]
}
```

### 步骤 8: 测试任务

```bash
# 使用 quickstart 进行最小化测试
python quickstart.py --provider_name vmware --path_to_vm "path/to/vm.vmx"

# 或使用 run.py 进行完整测试
python run.py \
    --provider_name docker \
    --path_to_vm Ubuntu/Ubuntu.vmx \
    --headless \
    --observation_type screenshot \
    --model gpt-4o \
    --max_steps 15 \
    --result_dir ./results \
    --client_password password
```

## 示例

### 示例 1: GIMP 图像编辑任务

```json
{
  "id": "7a4deb26-d57d-4ea9-9a73-630f66a7b568",
  "snapshot": "gimp",
  "instruction": "Could you tone down the brightness of my photo?",
  "source": "https://www.quora.com/How-do-I-edit-a-photo-in-GIMP",
  "config": [
    {
      "type": "download",
      "parameters": {
        "files": [
          {
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/gimp/7a4deb26-d57d-4ea9-9a73-630f66a7b568/woman_sitting_by_the_tree.png",
            "path": "/home/user/Desktop/woman_sitting_by_the_tree.png"
          }
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["gimp", "/home/user/Desktop/woman_sitting_by_the_tree.png"]
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["gimp"],
  "evaluator": {
    "postconfig": [
      {
        "type": "execute",
        "parameters": {
          "command": ["python3", "-c", "import pyautogui; pyautogui.hotkey(['shift', 'ctrl', 'e']);"]
        }
      },
      {
        "type": "sleep",
        "parameters": {"seconds": 0.5}
      },
      {
        "type": "execute",
        "parameters": {
          "command": ["python3", "-c", "import pyautogui; pyautogui.write(\"edited_darker\"); pyautogui.press(['enter']);"]
        }
      },
      {
        "type": "sleep",
        "parameters": {"seconds": 5}
      }
    ],
    "func": "check_brightness_decrease_and_structure_sim",
    "expected": {
      "type": "cloud_file",
      "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/gimp/7a4deb26-d57d-4ea9-9a73-630f66a7b568/woman_sitting_by_the_tree.png",
      "dest": "woman_sitting_by_the_tree.png"
    },
    "result": {
      "type": "vm_file",
      "path": "/home/user/Desktop/edited_darker.png",
      "dest": "edited_darker.png"
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 示例 2: Chrome 浏览器配置任务

```json
{
  "id": "bb5e4c0d-f964-439c-97b6-bdb9747de3f4",
  "snapshot": "chrome",
  "instruction": "Can you make Bing the main search engine when I look stuff up on the internet?",
  "source": "https://support.google.com/chrome/answer/95426",
  "config": [
    {
      "type": "launch",
      "parameters": {
        "command": ["google-chrome", "--remote-debugging-port=1337"]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["socat", "tcp-listen:9222,fork", "tcp:localhost:1337"]
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["chrome"],
  "evaluator": {
    "postconfig": [
      {
        "type": "launch",
        "parameters": {"command": ["pkill", "chrome"]}
      },
      {
        "type": "launch",
        "parameters": {"command": ["google-chrome", "--remote-debugging-port=1337"]}
      },
      {
        "type": "sleep",
        "parameters": {"seconds": 3}
      }
    ],
    "func": "match_in_list",
    "result": {
      "type": "default_search_engine"
    },
    "expected": {
      "type": "rule",
      "rules": {
        "expected": ["Microsoft Bing", "Bing"]
      }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 示例 3: LibreOffice Calc 表格任务

```json
{
  "id": "21df9241-f8d7-4509-b7f1-37e501a823f7",
  "snapshot": "libreoffice_calc",
  "instruction": "Change the representation of column \"Parameter\" to show in Millions (M) in Column B and Billions (B) in Column C. The numbers should be rounded to one decimal place, and half should be rounded up. Then remember to place a white space between the digits and the unit.",
  "source": "https://www.youtube.com/watch?v=p5C4V_AO1UU",
  "config": [
    {
      "type": "download",
      "parameters": {
        "files": [
          {
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_calc/21df9241-f8d7-4509-b7f1-37e501a823f7/Represent_in_millions_billions.xlsx",
            "path": "/home/user/Represent_in_millions_billions.xlsx"
          }
        ]
      }
    },
    {
      "type": "open",
      "parameters": {
        "path": "/home/user/Represent_in_millions_billions.xlsx"
      }
    }
  ],
  "trajectory": "trajectories/21df9241-f8d7-4509-b7f1-37e501a823f7",
  "related_apps": ["libreoffice_calc"],
  "evaluator": {
    "postconfig": [
      {
        "type": "activate_window",
        "parameters": {
          "window_name": "Represent_in_millions_billions.xlsx - LibreOffice Calc",
          "strict": true
        }
      },
      {
        "type": "execute",
        "parameters": {
          "command": ["python", "-c", "import pyautogui; pyautogui.hotkey(\"ctrl\", \"s\");"]
        }
      },
      {
        "type": "execute",
        "parameters": {
          "command": ["libreoffice", "--convert-to", "csv:Text - txt - csv (StarCalc):44,34,UTF-8,,,,false,true,true,false,false,1", "--outdir", "/home/user", "/home/user/Represent_in_millions_billions.xlsx"]
        }
      }
    ],
    "func": "compare_table",
    "result": {
      "type": "vm_file",
      "path": ["/home/user/Represent_in_millions_billions.xlsx", "/home/user/Represent_in_millions_billions-Sheet1.csv"],
      "dest": ["Represent_in_millions_billions.xlsx", "Represent_in_millions_billions-Sheet1.csv"],
      "multi": true
    },
    "expected": {
      "type": "cloud_file",
      "path": ["https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_calc/21df9241-f8d7-4509-b7f1-37e501a823f7/Represent_in_millions_billions_gold.xlsx", "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/libreoffice_calc/21df9241-f8d7-4509-b7f1-37e501a823f7/Represent_in_millions_billions_gold.csv"],
      "dest": ["Represent_in_millions_billions_gold.xlsx", "Represent_in_millions_billions_gold-Sheet1.csv"],
      "multi": true
    },
    "options": {
      "rules": [
        {
          "type": "sheet_print",
          "sheet_idx0": "RNSheet1",
          "sheet_idx1": "ENSheet1",
          "ignore_case": true
        }
      ]
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 示例 4: 操作系统终端任务

```json
{
  "id": "13584542-872b-42d8-b299-866967b5c3ef",
  "snapshot": "os",
  "instruction": "I click in terminal: terminal->132x43 to change terminal size but after each reboot terminal size is set to default setting and I have to change it again. Help me set it permanently",
  "source": "https://superuser.com/questions/72176/linux-set-default-terminal-size-and-screen-position",
  "config": [
    {
      "type": "execute",
      "parameters": {
        "command": ["python", "-c", "import pyautogui; import time; pyautogui.click({SCREEN_WIDTH_HALF}, {SCREEN_HEIGHT_HALF}); time.sleep(0.5);"]
      }
    }
  ],
  "related_apps": ["os"],
  "evaluator": {
    "postconfig": [
      {
        "type": "sleep",
        "parameters": {"seconds": 1}
      },
      {
        "type": "execute",
        "parameters": {
          "command": ["python", "-c", "import pyautogui; import time; time.sleep(0.5); pyautogui.hotkey('ctrl', 'alt', 't'); time.sleep(0.5); pyautogui.write('stty size'); time.sleep(0.5); pyautogui.press('enter')"]
        }
      }
    ],
    "func": "check_include_exclude",
    "result": {
      "type": "vm_terminal_output"
    },
    "expected": {
      "type": "rule",
      "rules": {
        "include": ["43 132"],
        "exclude": []
      }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 示例 5: 多应用协作任务

```json
{
  "id": "00fa164e-2612-4439-992e-157d019a8436",
  "snapshot": "libreoffice_writer",
  "instruction": "I need to include the experiment results from \"~/Documents/awesome-desktop/expe-results.xlsx\" into the currently writing report. Specifically, extract the results of GPT-4 and insert a table into the \"Main Results\" section of my report.",
  "source": "authors",
  "config": [
    {
      "type": "command",
      "parameters": {
        "command": ["mkdir", "-p", "/home/user/Documents/awesome-desktop/"]
      }
    },
    {
      "type": "download",
      "parameters": {
        "files": [
          {
            "path": "/home/user/Documents/awesome-desktop/awe_desk_env.docx",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/00fa164e-2612-4439-992e-157d019a8436/awe_desk_env.docx"
          },
          {
            "path": "/home/user/Documents/awesome-desktop/expe-results.xlsx",
            "url": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/00fa164e-2612-4439-992e-157d019a8436/results.xlsx"
          }
        ]
      }
    },
    {
      "type": "open",
      "parameters": {
        "path": "/home/user/Documents/awesome-desktop/awe_desk_env.docx"
      }
    }
  ],
  "trajectory": "trajectories/00fa164e-2612-4439-992e-157d019a8436",
  "related_apps": ["libreoffice_writer", "libreoffice_calc", "os"],
  "evaluator": {
    "postconfig": [
      {
        "type": "activate_window",
        "parameters": {
          "window_name": "awe_desk_env.docx - LibreOffice Writer",
          "strict": true
        }
      },
      {
        "type": "execute",
        "parameters": {
          "command": ["python", "-c", "import pyautogui; pyautogui.hotkey(\"ctrl\", \"s\");"]
        }
      }
    ],
    "func": "compare_docx_tables",
    "result": {
      "type": "vm_file",
      "path": "/home/user/Documents/awesome-desktop/awe_desk_env.docx",
      "dest": "awe_desk_env.docx"
    },
    "expected": {
      "type": "cloud_file",
      "path": "https://huggingface.co/datasets/xlangai/ubuntu_osworld_file_cache/resolve/main/multi_apps/00fa164e-2612-4439-992e-157d019a8436/awe_desk_env_gt.docx",
      "dest": "awe_desk_env_gt.docx"
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

## 最佳实践

### 1. 清晰的指令
- 具体说明期望结果
- 包含必要的上下文
- 避免歧义

### 2. 可复现的设置
- 使用版本化的文件 URL（如 HuggingFace）
- 指定精确的文件路径
- 在 config 中包含所有必要依赖

### 3. 健壮的评估
- 使用适当的评估函数
- 考虑边界情况
- 在适用时考虑多种有效解决方案

### 4. 文件托管
推荐的文件托管服务：
- **HuggingFace Datasets**: 研究推荐
- **GitHub Releases**: 适合版本化文件
- **自有服务器**: 确保长期可用性

## 测试清单

提交新任务前请确认：
- [ ] JSON 语法有效
- [ ] 所有必填字段存在
- [ ] 任务 ID 唯一（推荐 UUID 格式）
- [ ] 指令清晰无歧义
- [ ] Config 动作正确设置环境
- [ ] 评估函数存在且适当
- [ ] 参考文件可访问
- [ ] 任务已添加到 `test_all.json`
- [ ] 已通过 `quickstart.py` 或小批量测试
- [ ] 期望成功标准可衡量

## 相关资源

- `ACCOUNT_GUIDELINE.md` - Google 账号配置
- `PROXY_GUIDELINE.md` - 代理配置
- `desktop_env/evaluators/README.md` - 评估器设置详情
- `README.md` - OSWorld 概述
- `quickstart.py` - 最小化示例
