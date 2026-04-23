---
name: doc-organizer
label: 文档自动整理助手
description: 自动整理工作目录中的文档，按类型分类、重命名规范化、生成索引目录。当用户说"整理文档"、"归类文件"、"规范化文件名"、"生成文件索引"、"清理重复文件"时触发。
---

# 文档自动整理助手

## 功能

自动完成以下文档整理任务：
1. **文件分类** - 按类型（文档/代码/图片/数据等）自动归类
2. **命名规范化** - 统一命名格式（日期前缀、版本号等）
3. **重复检测** - 找出并标记重复文件
4. **索引生成** - 自动生成目录索引文件（README索引）
5. **目录结构化** - 创建标准目录结构

## 使用方式

### 触发指令
- "整理文档"
- "帮我归类文件"
- "规范化文件名"
- "生成文件索引"
- "清理重复文件"
- "整理 ~/Documents 目录"

### 参数
- `目录路径` - 要整理的目录（默认为当前工作目录）
- `分类规则` - 可选：按类型/日期/项目
- `命名格式` - 可选：日期前缀/版本号/自定义

## 工作流程

```
1. 扫描目标目录
   └─ 递归遍历所有文件
   
2. 文件分类
   ├─ 文档类：.md, .txt, .doc, .pdf
   ├─ 代码类：.py, .js, .ts, .java
   ├─ 图片类：.jpg, .png, .gif, .svg
   ├─ 数据类：.json, .csv, .db, .xlsx
   └─ 其他类：其他文件

3. 命名规范化
   ├─ 添加日期前缀：YYYY-MM-DD-filename
   ├─ 统一大小写：小写+连字符
   └─ 移除特殊字符

4. 重复检测
   └─ 基于文件哈希值比对

5. 生成索引
   └─ 生成 README.md 目录索引

6. 执行操作
   └─ 移动/重命名/生成索引文件
```

## 分类规则

### 默认分类
| 类别 | 扩展名 | 目标目录 |
|------|--------|---------|
| documents | .md, .txt, .doc, .docx, .pdf | docs/ |
| code | .py, .js, .ts, .java, .cpp, .go | src/ |
| images | .jpg, .jpeg, .png, .gif, .svg, .webp | images/ |
| data | .json, .csv, .db, .sqlite, .xlsx | data/ |
| archives | .zip, .tar, .gz, .rar | archives/ |
| others | 其他 | misc/ |

### 命名规范
```
默认格式：YYYY-MM-DD-descriptive-name.ext
示例：
  2026-04-23-project-proposal.md
  2026-04-23-data-analysis-v2.py
```

## 输出

```
📁 整理完成报告

📂 目录结构：
  docs/
    ├── 2026-04-23-meeting-notes.md
    └── 2026-04-23-requirements.docx
  src/
    ├── 2026-04-23-scraper-v2.py
    └── 2026-04-23-api-client.js
  images/
    └── 2026-04-23-screenshot.png
  data/
    └── 2026-04-23-export.csv

📊 统计：
  - 总文件数：42
  - 已分类：38
  - 已重命名：15
  - 重复文件：3（已标记）
  - 索引文件：已生成 README.md

⚠️ 注意事项：
  - 重复文件列表已保存至 duplicates.txt
  - 操作前已自动备份至 .backup-2026-04-23/
```

## 安全机制

1. **自动备份** - 操作前自动备份原文件
2. **预览模式** - 默认先预览，确认后执行
3. **可撤销** - 保留操作日志，支持撤销
4. **排除保护** - 自动排除 .git, node_modules 等目录

## 依赖

```bash
# Python 标准库，无需额外依赖
- os, shutil, hashlib, json, datetime
```

## 进阶用法

### 自定义分类规则
```python
rules = {
    "documents": [".md", ".txt", ".pdf"],
    "patents": [".pat", ".claim"],
    "reports": [".rpt", ".report"]
}
```

### 自定义命名格式
```python
# 格式：{date}-{project}-{type}-{version}
# 示例：2026-04-23-cabin-patent-v2.md
```
