---
name: qa
description: QA测试技能，确保测试覆盖率达到100%
license: MIT
---

# QA测试技能

## 触发场景

当需要为新功能编写测试或提升测试覆盖率时使用。

## 测试策略

### 1. 单元测试
- 测试单个函数/方法
- 隔离外部依赖
- 覆盖正常/异常路径

### 2. 集成测试
- 测试模块间交互
- 测试完整流程
- 使用测试数据库

### 3. 端到端测试
- 测试用户场景
- 验证业务流程

## 覆盖率目标

- 行覆盖率: 100%
- 分支覆盖率: 100%
- 函数覆盖率: 100%

## 测试规范

### 测试文件命名
```
tests/
├── unit/              # 单元测试
│   ├── test_game.py
│   └── test_hero.py
├── integration/       # 集成测试
│   └── test_api.py
└── conftest.py        # pytest配置
```

### 测试用例结构
```python
class TestFeatureName:
    """功能测试"""
    
    def test_normal_case(self):
        """测试正常场景"""
        # Given
        # When
        # Then
        
    def test_edge_case(self):
        """测试边界条件"""
        
    def test_error_case(self):
        """测试异常处理"""
```

## 执行流程

### 1. 获取覆盖率报告
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### 2. 分析未覆盖代码
- 识别未覆盖的行
- 分析未覆盖原因

### 3. 补充测试用例
- 为未覆盖代码编写测试
- 确保边界条件覆盖

### 4. 验证覆盖率
```bash
pytest tests/ --cov=src --cov-fail-under=100
```

## 输出报告

保存到 `docs/tests/coverage-report.md`
