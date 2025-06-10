# NFLAB 项目管理系统后端

基于 FastAPI 和 PostgreSQL 的现代化项目管理系统后端 API，专为建筑效果图渲染公司设计。

## 功能特性

- 🚀 **现代化技术栈**: FastAPI + PostgreSQL + SQLAlchemy 2.0
- 🔐 **JWT 认证**: 安全的用户认证和授权系统
- 📊 **项目管理**: 完整的项目生命周期管理
- 👥 **客户管理**: 详细的客户信息和关系管理
- 🏢 **团队管理**: 团队成员和工作量管理
- 💰 **财务管理**: 收入、成本和利润分析
- 🌐 **多币种支持**: 支持 8 种主要货币
- 🌍 **国际化**: 中英文双语支持
- 📈 **数据可视化**: 仪表板和报表功能

## 技术栈

- **Web框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL (with AsyncPG) / SQLite (开发)
- **ORM**: SQLAlchemy 2.0 (异步)
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt
- **数据迁移**: Alembic
- **数据验证**: Pydantic v2
- **文档生成**: 自动生成 OpenAPI 文档

## 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 12+ (生产环境)
- Redis (可选，用于缓存)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 数据库配置

1. 创建数据库:
```sql
CREATE DATABASE nflab;
```

2. 配置环境变量:
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置你的数据库连接信息
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head

# 创建管理员账户
python create_admin.py
```

### 启动服务

```bash
# 开发模式
python app/main.py

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 应用配置
│   │   ├── database.py        # 数据库连接
│   │   └── security.py        # 安全认证
│   ├── models/                 # 数据库模型
│   │   ├── __init__.py
│   │   ├── base.py            # 基础模型
│   │   ├── user.py            # 用户模型
│   │   ├── project.py         # 项目模型
│   │   ├── client.py          # 客户模型
│   │   └── team.py            # 团队模型
│   ├── schemas/                # Pydantic 模型
│   │   ├── common.py          # 通用模型
│   │   ├── auth.py            # 认证模型
│   │   ├── project.py         # 项目模型
│   │   ├── client.py          # 客户模型
│   │   └── dashboard.py       # 仪表板模型
│   └── api/                    # API 路由
│       ├── deps.py            # 依赖项
│       └── v1/                # API v1
│           ├── auth.py        # 认证路由
│           ├── projects.py    # 项目管理路由
│           ├── clients.py     # 客户管理路由
│           └── dashboard.py   # 仪表板路由
├── alembic/                    # 数据库迁移
├── requirements.txt            # Python 依赖
├── alembic.ini                # Alembic 配置
├── create_admin.py            # 管理员创建脚本
├── README.md                  # 项目文档
└── nflab.db                   # SQLite 数据库文件
```

## API 接口

### 认证模块
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/profile` - 获取用户信息
- `PUT /api/auth/profile` - 更新用户信息

### 项目管理模块
- `GET /api/projects/` - 获取项目列表
- `POST /api/projects/` - 创建项目
- `GET /api/projects/{id}` - 获取项目详情
- `PUT /api/projects/{id}` - 更新项目
- `DELETE /api/projects/{id}` - 删除项目
- `PUT /api/projects/{id}/status` - 更新项目状态
- `PUT /api/projects/{id}/progress` - 更新项目进度
- `GET /api/projects/gantt/data` - 获取甘特图数据

### 客户管理模块
- `GET /api/clients/` - 获取客户列表
- `POST /api/clients/` - 创建客户
- `GET /api/clients/{id}` - 获取客户详情
- `PUT /api/clients/{id}` - 更新客户
- `DELETE /api/clients/{id}` - 删除客户
- `GET /api/clients/{id}/projects` - 获取客户项目
- `PUT /api/clients/{id}/project-history` - 更新客户项目历史

### 仪表板模块
- `GET /api/dashboard/stats` - 获取仪表板统计数据
- `GET /api/dashboard/finance/overview` - 获取财务概览
- `GET /api/dashboard/settings/exchange-rates` - 获取汇率数据

## 开发指南

### 添加新的API模块

1. 在 `app/models/` 下创建数据库模型
2. 在 `app/schemas/` 下创建 Pydantic 模型
3. 在 `app/api/v1/` 下创建路由
4. 在 `app/main.py` 中注册路由
5. 生成并执行数据库迁移

### 数据库操作

```python
# 异步查询示例
from sqlalchemy import select
from app.models.user import User

async def get_user_by_id(db: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### 认证装饰器

```python
from app.api.deps import get_current_active_user, require_permission

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_active_user)
):
    return {"message": f"Hello {current_user.name}"}
```

## 数据模型

### 核心实体关系

```
用户 (User) ←→ 认证授权
    ↓
项目 (Project) ←→ 客户 (Client)
    ↓
团队成员 (TeamMember) ←→ 工作分配
    ↓
财务记录 (FinanceRecord) ←→ 收入成本
```

### 支持的枚举值

**项目状态**: reporting, modeling, rendering, delivering, completed, cancelled
**付款状态**: unpaid, partial, paid, overdue
**货币类型**: USD, EUR, AUD, CNY, CAD, GBP, SGD, AED
**用户角色**: admin, manager, designer, modeler, renderer, sales
**客户地区**: Asia-Pacific, North America, Europe, Middle East, Africa, South America

## 示例数据

系统包含以下示例数据：

### 客户
- **URBIS** (澳洲客户) - 商业地产开发
- **万科集团** (中国客户) - 住宅项目开发

### 项目
- **Sydney CBD Tower** - 悉尼CBD高层写字楼 (AUD $45,000)
- **万科翡翠公园** - 高端住宅小区景观 (CNY ¥280,000)

### 团队成员
- **张建模** - 建模部门专家
- **李渲染** - 渲染部门专家

## 部署

### Docker 部署

```bash
# 构建镜像
docker build -t nflab-api .

# 运行容器
docker run -p 8000:8000 nflab-api
```

### 生产环境配置

1. 设置 `DEBUG=False`
2. 配置安全的 `SECRET_KEY`
3. 使用 HTTPS
4. 配置反向代理 (Nginx)
5. 设置监控和日志

## 性能优化

- 数据库查询优化和索引
- Redis 缓存策略
- 异步处理和连接池
- API 响应时间监控
- 分页查询和数据压缩

## 安全措施

- JWT 令牌认证
- 密码哈希加密
- CORS 跨域保护
- SQL 注入防护
- API 访问频率限制

## 测试

### 运行测试

```bash
# API 基础测试
python -c "
import requests
response = requests.get('http://localhost:8000/health')
print(f'健康检查: {response.json()}')"

# 认证测试
python -c "
import requests
login = requests.post('http://localhost:8000/api/auth/login', 
                     json={'username': 'admin', 'password': 'admin123'})
print(f'登录状态: {login.status_code}')"
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 提交代码 (`git commit -m 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 发起 Pull Request

## 许可证

MIT License

## 联系方式

- 项目地址: https://github.com/nflab/project-management-api
- 技术支持: support@nflab.com
- 文档更新: 2025-06-03 