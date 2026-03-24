# zvec Claude Memory Plugin

基于 **zvec 嵌入式向量数据库**的 Claude Code 记忆插件。

- **混合架构**: Session hooks + explicit skills，灵活的内存管理
- **SessionStart Hook**: 初始化内存会话和状态
- **SessionEnd Hook**: 提交会话并优化集合以提升性能
- **Skills**: 使用 `memory-recall`、`memory-store` 和 `memory-forget` 进行显式控制
- **向量化存储**: 使用 zvec 进行高效的相似度搜索
- **多种嵌入提供者**: 支持 OpenAI 及与其兼容的厂商（如 DashScope、Sentence Transformers）
- **本地存储**: 嵌入式数据库，无需外部依赖

## 功能特性

- **显式内存控制**: 通过 skills 手动存储、召回和遗忘记忆
- **向量搜索**: 基于语义相似度的记忆检索
- **持久化存储**: 跨所有会话的长期记忆
- **分类支持**: 按类别组织记忆（决策、修复、偏好等）

## 设计选择

- **存储**: 嵌入式 zvec 向量数据库
- **模式**: 仅本地（无需 HTTP 服务器）
- **配置**: 全局配置文件位于 `~/.zvec/zvec.conf`
- **内存目录**: 通过 zvec.conf 中的 `dbPath` 配置（默认：`~/.zvec/memory.zvec`）

## 目录结构

```
claude-memory-plugin/
├── hooks/
│   ├── hooks.json
│   ├── session-start.sh      # 初始化会话
│   └── session-end.sh        # 提交并优化集合
├── scripts/
│   ├── memory_zvec.py        # 主要内存桥接脚本
│   └── test_memory_zvec.py   # 测试脚本
├── skills/
│   ├── memory-recall/
│   │   └── SKILL.md          # 从长期存储中检索记忆
│   ├── memory-store/
│   │   └── SKILL.md          # 存储重要信息
│   ├── memory-forget/
│   │   └── SKILL.md          # 删除特定记忆
├── example.zvec.conf
└── README.md
```

## 配置

全局配置文件位于 `~/.zvec/zvec.conf`:

```bash
mkdir -p ~/.zvec/
cp example.zvec.conf ~/.zvec/zvec.conf
# 编辑 ~/.zvec/zvec.conf 填入你的 API 密钥
```

```json
{
  "embedding": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "apiKey": "sk-your-openai-key",
    "apiUrl": "https://api.openai.com/v1/embeddings"
  },
  "dbPath": "~/.zvec/memory/database",
  "autoCapture": true,
  "autoRecall": true,
  "captureMaxChars": 500
}
```

### 配置选项

- `embedding.provider`: `"openai"` 或 `"sentence-transformers"`
- `embedding.model`: 嵌入模型名称（默认：`"text-embedding-3-small"`）
- `embedding.apiKey`: 嵌入服务的 API 密钥
- `embedding.apiUrl`: 自定义 API 端点（可选）
- `dbPath`: zvec 数据库路径（默认：`"~/.zvec/memory/database"`）
- `autoRecall`: 启用自动记忆注入（默认：`true`）

## Hook 行为

- `SessionStart`
  - 验证 `zvec.conf` 是否存在
  - 初始化全局数据库路径
  - 返回 Claude 上下文的会话信息
- `SessionEnd`
  - 创建记忆集合（如果不存在，带有正确的 schema）
  - 调用 `collection.optimize()` 提升查询性能
  - 提交会话数据并报告记忆数量

## Skills

所有 skills 都使用 `${CLAUDE_PLUGIN_ROOT}` 环境变量的相对路径以保证可移植性。

### memory-recall

当你需要关于用户偏好、历史或个人信息的上下文时，从长期存储中搜索和检索相关记忆。

**使用场景：**
```
当以下情况时使用 memory-recall：
- 需要访问长期存储中的用户记忆
- 回忆用户偏好、兴趣或个人背景
- 获取可能相关的用户背景信息
- 检索之前保存的历史上下文
```

**示例：**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py recall --query "authentication fix" --top-k 5 --task-id "$TASK_ID"
```

### memory-store

在长期记忆中存储重要信息。当用户想要记住特定内容、为未来会话做笔记或明确保存知识时使用。

**使用场景：**
```
当以下情况时使用 memory-store：
- 用户要求你记住特定内容
- 做出重要决定时
- 发现关键修复或解决方案时
- 应该保存用户偏好时
```

**分类：**
- `preference`: 用户喜欢/不喜欢
- `decision`: 重要决定
- `fix`: 问题解决方案
- `fact`: 事实信息
- `general`: 默认分类

**示例：**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py store --text "使用 JWT 令牌进行身份验证" --category "decision" --task-id "$TASK_ID"
```

### memory-forget

从长期存储中删除特定记忆。当用户想要删除过时信息、错误记忆或不再相关的数据时使用。

**使用场景：**
```
当以下情况时使用 memory-forget：
- 用户要求删除特定信息
- 需要删除过时或不正确的记忆
- 清理废弃数据
```

**重要提示：**
- 删除记忆前务必获得用户明确确认
- 搜索要删除的记忆时，显示所有匹配项并让用户选择
- 记忆 ID 格式：`m_<12 位十六进制字符>`
- 告知用户删除是永久性的

**示例：**
```bash
# 按记忆 ID 删除
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py forget --memory-id "m_abc123def456" --task-id "$TASK_ID"

# 先搜索，再删除
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_zvec.py recall --query "outdated info" --top-k 10
```

## 安装

1. 快速安装（插件市场）
```bash
/plugin marketplace add chinaux/zvec-agent-plugins
/plugin install memory-zvec
```

2. 本地安装：
```bash
git clone https://github.com/chinaux/zvec-agent-plugins.git
cd zvec-agent-plugins
claude --plugin-dir ./claude-memory-plugin
```

3. 创建配置文件：
```bash
mkdir -p ~/.zvec/
cp example.zvec.conf ~/.zvec/zvec.conf
# 编辑 ~/.zvec/zvec.conf 填入你的设置
```

4. 插件将自动被 Claude Code 加载。

## API 参考

### 命令行接口

使用全局配置文件 `~/.zvec/zvec.conf`：

**存储记忆：**
```bash
python3 scripts/memory_zvec.py store \
  --text "<记忆文本>" \
  --category "<分类>"
```

**召回记忆：**
```bash
python3 scripts/memory_zvec.py recall \
  --query "<搜索查询>" \
  --top-k <结果数量>
```

**遗忘记忆：**
```bash
python3 scripts/memory_zvec.py forget \
  --memory-id "<记忆 ID>"
```

**API 响应格式：**

所有命令返回 JSON 到 stdout：

**成功：**
```json
{
  "ok": true,
  "status_line": "[memory-zvec] 操作成功",
  ...
}
```

**错误：**
```json
{
  "ok": false,
  "status_line": "[memory-zvec] 错误描述"
}
```

## 注意事项

- 此插件需要安装 zvec Python 包
- 数据库文件本地存储在 `.zvec/memory/database/` 中
- 所有会话共享同一个全局数据库用于长期记忆
- 记忆 ID 格式：`m_<12 位十六进制字符>`
- 所有 skills 使用 `${CLAUDE_PLUGIN_ROOT}` 实现可移植路径
- 脚本内置错误处理，失败时通过 stderr 警告
- 无调试日志 - 生产就绪代码

## 故障排除

常见问题：

1. **"zvec not available"**: 安装 zvec Python 包
   ```bash
   pip install zvec
   ```

2. **配置错误**: 检查 `zvec.conf` 语法和必需字段

3. **权限错误**: 确保对 `.zvec/memory/database/` 目录有写入权限

4. **记忆未找到**: 验证记忆 ID 格式（`m_<12 位十六进制字符>`）

5. **没有记忆被召回**: 确保配置中启用了 autoRecall

## 许可证

Apache 2.0
