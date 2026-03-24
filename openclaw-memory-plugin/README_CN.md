# memory-zvec Plugin

OpenClaw 内存插件，使用 zvec 作为嵌入式向量数据库进行长期记忆存储和检索。

## 功能特性

- **向量存储**: 使用 zvec 进行高效的向量相似度搜索
- **自动召回**: 自动将相关记忆注入到 agent 上下文中
- **自动捕获**: 自动捕获对话中的重要信息
- **多种工具**: 提供 `memory_recall`、`memory_store` 和 `memory_forget` 工具
- **完善的资源管理**: 正确的集合生命周期管理
- **健壮的错误处理**: 全面的错误处理和空值验证

## 目录结构

```
openclaw-memory-plugin/
├── index.ts              # 主插件入口
├── config.ts             # 配置 schema 和工具函数
├── memory-db.ts          # 数据库抽象层
├── index.test.ts         # 单元测试
├── integration.test.ts   # 集成测试
├── switch-memory.sh      # 插槽切换脚本
├── package.json          # 依赖和脚本
├── tsconfig.json         # TypeScript 配置
└── README.md             # 文档
```

## 快速安装
```bash
openclaw plugins install @zvec-ai/memory-zvec
```

## 本地安装

```bash
git clone https://github.com/zvec-ai/agent-plugins.git
cd openclaw-memory-plugin
# 构建插件
pnpm install && pnpm clean && pnpm build

# 创建 npm 包
npm pack

# 安装到 OpenClaw
openclaw plugins install ./memory-zvec-*.tgz
```
## 配置

在 `~/.openclaw/openclaw.json` 中配置：

```json
{
  "plugins": {
    "entries": {
      "memory-zvec": {
        "enabled": true,
        "config": {
          "embedding": {
            "provider": "openai",
            "apiKey": "${OPENAI_API_KEY}",
            "model": "text-embedding-3-small",
            "baseUrl": "https://api.openai.com/v1/embeddings"
          },
          "dbPath": "~/.openclaw/memory/zvec",
          "autoCapture": true,
          "autoRecall": true
        }
      }
    },
    "slots": {
      "memory": "memory-zvec"
    }
  }
}
```

设置 API 密钥：
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 配置选项

**必需设置：**
- `embedding.provider`: 嵌入提供者 (`openai` 等)
- `embedding.apiKey`: API 密钥
- `embedding.model`: 嵌入模型名称

**可选设置：**
- `dbPath`: zvec 数据库存储路径 (默认：`~/.openclaw/memory/zvec`)
- `autoCapture`: 启用自动记忆捕获 (默认：`true`)
- `autoRecall`: 启用自动记忆召回 (默认：`true`)
- `captureMaxChars`: 自动捕获的最大消息长度 (默认：`500`)

## 使用

### 工具

#### memory_recall
搜索长期记忆。
```json
{
  "name": "memory_recall",
  "parameters": {
    "query": "user preferences",
    "limit": 5
  }
}
```

#### memory_store
保存重要信息到长期记忆。
```json
{
  "name": "memory_store",
  "parameters": {
    "text": "User prefers dark mode",
    "importance": 0.8,
    "category": "preference"
  }
}
```

#### memory_forget
删除特定记忆。
```json
{
  "name": "memory_forget",
  "parameters": {
    "memoryId": "uuid-of-memory-to-delete"
  }
}
```

### 记忆分类

- `preference`: 用户偏好
- `fact`: 事实信息
- `decision`: 过去的决定
- `entity`: 联系信息和实体引用
- `other`: 其他杂项信息

### 自动捕获触发器

插件会在检测到以下内容时自动捕获：
- 明确的记住/保存指令
- 偏好表达
- 决定陈述
- 联系信息（电话、邮箱）
- 重要声明

## ZVec 集成

使用官方 [@zvec/zvec](https://www.npmjs.com/package/@zvec/zvec) 包进行向量数据库操作。

**特性：**
- 真实的向量数据库：使用 Zvec 的 HNSW 索引进行快速相似度搜索
- 多种距离度量：支持余弦相似度和 L2 距离
- 基于 schema 的存储： alongside vectors 存储文本、重要性、类别和时间戳
- 高效操作：原生性能，内存映射 I/O
- 完善的资源管理和错误处理

## 开发和测试

```bash
# 安装依赖
pnpm install

# 构建项目
pnpm build

# 运行所有测试
pnpm test

# 运行单元测试
pnpm test:unit

# 运行集成测试
pnpm test:integration

# 监听模式开发
pnpm dev

# 清理构建产物
pnpm clean
```

### 实时测试

```bash
# 设置 OpenAI API 密钥
export OPENAI_API_KEY="your-api-key-here"

# 运行包含实时 API 测试的所有测试
pnpm test
```

## 故障排除

**问题**: "vector indexer not found for field: embedding"
- **解决**: 删除数据库目录并重启

**问题**: 权限错误
- **解决**: 确保数据库目录有正确的读写权限

**问题**: 内存使用过高
- **解决**: 减少 `captureMaxChars` 限制内存消耗

**问题**: 搜索性能慢
- **解决**: 确保系统有足够 RAM，数据库目录在快速存储设备上

### 调试日志

```bash
# 设置日志级别为 debug
export OPENCLAW_LOG_LEVEL=debug

# 运行 OpenClaw 并观察 memory-zvec 相关日志
openclaw gateway run
```

## 发布

```bash
# 更新 package.json 中的版本号

# 运行完整测试套件
pnpm clean && pnpm install && pnpm test && pnpm build

# 登录 npm
npm login

# 发布
npm publish --access public
```

## 许可证

Apache 2.0
