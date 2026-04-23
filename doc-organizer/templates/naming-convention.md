# 文件命名规范

## 标准格式

```
{YYYY-MM-DD}-{descriptive-name}-{version}.{ext}
```

## 示例

### 文档类
```
2026-04-23-project-proposal-v2.md
2026-04-23-meeting-notes.md
2026-04-23-requirements-spec.md
```

### 代码类
```
2026-04-23-data-scraper-v3.py
2026-04-23-api-client.js
2026-04-23-config-parser.go
```

### 数据类
```
2026-04-23-sales-data-q1.csv
2026-04-23-user-export.json
2026-04-23-analysis-results.xlsx
```

## 命名规则

1. **日期前缀** - 使用文件创建或修改日期
2. **描述性名称** - 小写字母，连字符分隔
3. **版本号** - 可选，使用 v1, v2, v3
4. **扩展名** - 小写

## 禁止事项

- ❌ 空格：`my file.txt`
- ❌ 特殊字符：`file@#$%.txt`
- ❌ 中文文件名：`文档.txt`
- ❌ 无意义名称：`1.txt`, `新建文本文档.txt`
- ❌ 过长名称（超过50个字符）

## 最佳实践

- ✅ 使用动词开头：`analyze-`, `generate-`, `export-`
- ✅ 包含项目名：`cabin-patent-framework.md`
- ✅ 包含类型：`report-`, `draft-`, `final-`
