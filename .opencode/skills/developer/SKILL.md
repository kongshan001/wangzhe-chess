---
name: developer
description: 开发技能，根据需求文档实现功能代码
license: MIT
---

# 开发技能

## 触发场景

当有新的功能需求文档需要实现时使用。

## 执行步骤

### 1. 需求分析
- 阅读 `docs/requirements/` 中的需求文档
- 理解功能目标和技术要求
- 识别涉及的模块

### 2. 方案设计
- 设计代码结构
- 确定修改点
- 评估影响范围

### 3. 代码实现
- 遵循项目编码规范
- 编写清晰的代码
- 添加必要的注释

### 4. 自测验证
- 运行相关测试
- 验证功能正确性
- 检查边界情况

## 编码规范

### Python
```python
def function_name(param: Type) -> ReturnType:
    """函数描述
    
    Args:
        param: 参数描述
        
    Returns:
        返回值描述
    """
    pass
```

### 文件结构
```
src/server/
├── api/           # REST API
├── ws/            # WebSocket
├── game/          # 游戏逻辑
├── models/        # 数据模型
└── services/      # 业务服务
```

## 检查清单

- [ ] 代码符合 PEP 8
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 无硬编码配置
- [ ] 异常处理完善
- [ ] 日志记录适当
