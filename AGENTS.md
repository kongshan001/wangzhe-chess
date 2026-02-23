# 王者之奕 - 项目规范

## 项目概述

王者之奕是一个生产级自走棋（Auto Chess）游戏服务端，采用 Python + FastAPI 技术栈，支持 8 人在线对战。

## 技术栈

- **框架**: FastAPI + Uvicorn
- **数据库**: MySQL 8.0 + SQLAlchemy + Alembic
- **缓存**: Redis 7.2
- **WebSocket**: python-socketio
- **测试**: pytest + pytest-asyncio

## 项目结构

```
wangzhe-chess/
├── src/
│   ├── server/
│   │   ├── api/           # REST API 端点
│   │   ├── ws/            # WebSocket 处理器
│   │   ├── game/          # 游戏核心逻辑
│   │   │   ├── battle/    # 战斗系统
│   │   │   ├── hero_pool.py
│   │   │   ├── synergy.py
│   │   │   └── economy.py
│   │   ├── room/          # 房间管理
│   │   ├── match/         # 匹配系统
│   │   ├── models/        # 数据模型
│   │   └── db/            # 数据库连接
│   └── shared/
│       ├── protocol/      # 通信协议
│       ├── constants.py
│       └── models.py
├── tests/
│   ├── unit/              # 单元测试
│   └── integration/       # 集成测试
├── docs/
│   ├── requirements/      # 需求文档
│   ├── reviews/           # 代码审核报告
│   ├── tests/             # 测试报告
│   ├── api/               # API 文档
│   ├── architecture.md
│   └── core-classes.md
├── config/                # 配置模块
├── migrations/            # 数据库迁移
└── .opencode/
    ├── agents/            # 自定义 agents
    └── skills/            # 自定义 skills
```

## 编码规范

### Python 规范

- 使用 Python 3.11+
- 遵循 PEP 8 代码风格
- 使用 type hints
- 行长度限制: 100 字符

### 命名约定

| 类型 | 命名风格 | 示例 |
|------|----------|------|
| 类 | PascalCase | `HeroPool` |
| 函数/方法 | snake_case | `get_hero_by_id` |
| 变量 | snake_case | `player_count` |
| 常量 | UPPER_SNAKE_CASE | `MAX_PLAYERS` |
| 私有方法 | _leading_underscore | `_calculate_damage` |

### 文档字符串

```python
def function_name(param: Type) -> ReturnType:
    """简短描述。
    
    详细描述（可选）。
    
    Args:
        param: 参数描述
        
    Returns:
        返回值描述
        
    Raises:
        Exception: 异常描述
    """
```

### 导入顺序

```python
# 1. 标准库
import os
from typing import Optional

# 2. 第三方库
import fastapi
from sqlalchemy import Column

# 3. 本地模块
from src.server.game import Hero
```

## Git 提交规范

使用 Conventional Commits:

```
<type>(<scope>): <description>
```

### 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档变更
- `test`: 测试相关
- `refactor`: 重构
- `perf`: 性能优化
- `chore`: 其他

### 示例

```
feat(hero): 添加英雄升级功能
fix(battle): 修复伤害计算溢出问题
docs(api): 更新 WebSocket 协议文档
test(economy): 添加经济系统单元测试
```

## 测试规范

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 运行特定测试
pytest tests/unit/test_hero.py -v
```

### 测试命名

```python
class TestFeatureName:
    def test_normal_case(self):
        """测试正常场景"""
        
    def test_edge_case(self):
        """测试边界条件"""
        
    def test_error_case(self):
        """测试异常处理"""
```

## 启动服务

```bash
# 开发模式
.venv/bin/uvicorn src.server.main:app --reload --port 8000

# 或使用项目命令
.venv/bin/wangzhe-server
```

## 关键命令

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码格式化
ruff format src/

# 类型检查
mypy src/

# 数据库迁移
alembic upgrade head
```

## 工作流程

项目使用自动化流水线，只需提出需求愿景，系统会自动：

1. **需求分析** - 生成 docs/requirements/*.md
2. **代码实现** - 修改源代码
3. **代码审核** - 生成 docs/reviews/*.md
4. **测试覆盖** - 确保覆盖率 100%
5. **文档更新** - 更新 docs/ 目录
6. **Git 提交** - 自动提交并推送

## 注意事项

- 所有新功能必须有对应的测试
- 提交前确保所有测试通过
- 遵循现有的代码风格和架构
- 敏感信息（密钥、密码）不要提交到代码库
