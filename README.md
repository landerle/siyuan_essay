# 📝 我的作文管理工具

一个面向学生个人使用的本地作文管理工具，支持作文导入、分类、编辑、导出及 AI 分析。

## 功能特性

### ✅ 第一期（已实现）

- 📂 **多种导入方式**
  - 从本地选择文件上传（自动归档）
  - 扫描作文目录导入
  - 增量扫描（仅新增）& 全量重新扫描
- 🏷️ **智能分类与标签**
  - 自动分类（亲情类 / 成长感悟类 / 校园生活类 / 其他）
  - 自动提取摘要、统计字数
- 🔍 **搜索与筛选**（侧边栏统一管理）
  - 关键词搜索
  - 按分类 / 标签筛选
- ✏️ **在线编辑与保存**
  - 支持修改标题和正文
  - 保存时自动重新统计字数
- 📥 **导出功能**
  - 单篇导出（作文详情页）
  - 批量多选导出（合并为一个文件）
- 🗑️ **删除管理**
  - 带确认弹框的删除操作
  - 同时删除数据库记录与本地文件
- 🌟 **优秀句段收藏**
  - AI 推荐的句子一键收藏
  - 手动任意句子收藏
  - 独立的收藏夹页面（支持分类 / 标签筛选）
  - 收藏导出为文本文件
- 💾 **SQLite 数据库持久化**
  - 增量保存，每次启动无需重新扫描
- 🌐 **美观的 Streamlit 网页界面**
  - 5 个标签页（首页 / 作文列表 / 作文详情 / 优秀句段收藏 / 设置）
- 🤖 **AI 作文分析**（需配置 API Key）
  - 一键分析作文优缺点、改进建议
  - 自动推荐优秀句段并支持一键收藏
  - 连接测试与环境诊断功能
  - 支持 DeepSeek / OpenAI 等兼容接口

## 安装依赖

```bash
pip install -r requirements.txt
```

**可选依赖**（如需 AI 分析功能）：
```bash
pip install openai
```

## 如何运行

### 方式一（推荐）
双击运行 `start_app.bat`

### 方式二（命令行）
```bash
streamlit run app.py
```

运行后，浏览器访问 `http://localhost:8501`

## 首次使用

1. **导入作文**
   - 方式 A：在「首页」点击「从本地选择文件导入」上传 `.txt` / `.docx` 文件
   - 方式 B：将文件放入 `data/compositions/` 目录，点击「扫描新增作文」
2. **浏览与管理**
   - 「作文列表」查看所有作文，支持搜索、筛选、删除
   - 「作文详情」查看全文，支持编辑、导出
3. **AI 分析**（需配置 API Key）
   - 在「设置」页面填入 DeepSeek API Key
   - 在「作文详情」页点击「AI 分析作文」
4. **收藏句段**
   - AI 分析结果中的优秀句子可一键收藏
   - 也可手动选中任意句子收藏
   - 在「优秀句段收藏」标签页统一管理

## 配置说明

- `config.json` — API Key 等用户配置（**请勿提交到 Git**）
- `config.json.example` — 配置模板
- `data/database.db` — SQLite 数据库文件（自动创建）

## 项目结构

```
├── app.py                     # Streamlit 主应用
├── config.py                  # 全局配置（路径、常量）
├── config.json                # 用户配置（API Key 等）
├── config.json.example        # 配置模板
├── requirements.txt           # 依赖列表
├── start_app.bat              # 快捷启动脚本
├── modules/
│   ├── database.py            # 数据库操作（CRUD）
│   ├── file_reader.py         # 文件读取（txt / docx）
│   ├── file_scanner.py        # 目录扫描与导入
│   ├── analyzer.py            # 规则分析（分类、标签、摘要）
│   ├── llm_client.py          # AI 客户端（OpenAI 兼容接口）
│   └── utils.py               # 工具函数
├── data/
│   ├── compositions/          # 作文归档目录
│   └── database.db            # SQLite 数据库
└── prompts/                   # 提示词模板（预留）
```

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.x | 运行环境 |
| Streamlit | Web 界面框架 |
| SQLite | 本地数据库 |
| python-docx | .docx 文件解析 |
| pandas | 数据处理与展示 |
| OpenAI SDK | AI 分析（可选） |
