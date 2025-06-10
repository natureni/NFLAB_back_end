# NFLAB 项目管理系统 - 后端接口需求文档

## 1. 系统概述

NFLAB是一个专为建筑效果图渲染公司设计的综合项目管理系统，主要功能包括项目管理、客户管理、团队管理、财务管理等模块。系统支持多币种、多语言、权限管理等企业级功能。

### 1.1 技术栈要求
- **认证方式**: JWT Token 认证
- **数据格式**: JSON
- **文件上传**: 支持 Excel、PDF 等格式
- **多币种支持**: USD, EUR, AUD, CNY, CAD, GBP, SGD, AED
- **国际化**: 支持中英文

### 1.2 通用响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2025-01-27T10:30:00Z"
}
```

## 2. 认证与权限管理模块

### 2.1 用户认证接口

#### POST /api/auth/login
用户登录接口
```json
// 请求
{
  "username": "admin",
  "password": "admin123",
  "remember": true
}

// 响应
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "1",
      "username": "admin",
      "name": "系统管理员",
      "email": "admin@nflab.com",
      "role": "admin",
      "department": "管理部",
      "avatar": "avatar_url",
      "lastLoginAt": "2025-01-27T10:30:00Z",
      "status": "active"
    },
    "permissions": [
      {
        "module": "dashboard",
        "actions": ["view", "create", "edit", "delete", "export"]
      }
    ]
  }
}
```

#### POST /api/auth/logout
用户登出接口

#### GET /api/auth/profile
获取当前用户信息

#### PUT /api/auth/profile
更新用户信息

### 2.2 权限管理接口

#### GET /api/permissions/roles
获取角色权限配置

#### PUT /api/permissions/roles/{roleId}
更新角色权限

## 3. 项目管理模块

### 3.1 项目CRUD接口

#### GET /api/projects
获取项目列表
```json
// 查询参数
{
  "page": 1,
  "pageSize": 20,
  "status": "rendering", // reporting, modeling, rendering, delivering
  "client": "万科集团",
  "search": "搜索关键词",
  "startDate": "2025-01-01",
  "endDate": "2025-12-31"
}

// 响应
{
  "code": 200,
  "data": {
    "list": [
      {
        "id": "NF2501",
        "name": "Sydney CBD Tower",
        "protocolNumber": "NF2501",
        "client": "Bathurst开发公司",
        "status": "reporting",
        "deadline": "2025-03-15",
        "budget": 45000,
        "currency": "AUD",
        "exchangeRate": 4.78,
        "budgetCNY": 215100,
        "paymentStatus": "unpaid",
        "progress": 8,
        "type": "商业综合体",
        "services": [
          {
            "camera": "Bird's Eye View",
            "qty": 3,
            "unitPrice": 8000,
            "price": 24000
          }
        ],
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-27T10:30:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

#### POST /api/projects
创建新项目

#### GET /api/projects/{id}
获取项目详情

#### PUT /api/projects/{id}
更新项目信息

#### DELETE /api/projects/{id}
删除项目

### 3.2 项目状态管理

#### PUT /api/projects/{id}/status
更新项目状态

#### PUT /api/projects/{id}/progress
更新项目进度

### 3.3 合同管理

#### GET /api/projects/{id}/contract
获取项目合同信息

#### POST /api/projects/{id}/contract/generate
生成合同PDF

#### GET /api/projects/services/templates
获取服务项目模板

### 3.4 甘特图接口

#### GET /api/projects/gantt
获取甘特图数据
```json
{
  "code": 200,
  "data": [
    {
      "id": "NF2501",
      "name": "Sydney CBD Tower",
      "start": "2025-01-01",
      "end": "2025-03-15",
      "progress": 8,
      "dependencies": [],
      "tasks": [
        {
          "id": "task1",
          "name": "需求分析",
          "start": "2025-01-01",
          "end": "2025-01-07",
          "progress": 100
        }
      ]
    }
  ]
}
```

## 4. 客户管理模块

### 4.1 客户CRUD接口

#### GET /api/clients
获取客户列表
```json
// 查询参数
{
  "page": 1,
  "pageSize": 20,
  "region": "Asia-Pacific",
  "status": "active",
  "search": "搜索关键词"
}

// 响应数据结构
{
  "id": "C001",
  "companyName": "URBIS",
  "companyNameCN": "优比思",
  "contactPerson": "John Smith",
  "contactPersonCN": "约翰·史密斯",
  "title": "Project Manager",
  "titleCN": "项目经理",
  "email": "john@urbis.com.au",
  "phone": "+61 7 3007 3800",
  "fax": "+61 7 3007 3801",
  "website": "https://urbis.com.au",
  "businessAddress": {
    "street": "Level 15, 500 Queen Street",
    "city": "Brisbane",
    "state": "QLD",
    "postcode": "4000",
    "country": "Australia"
  },
  "region": "Asia-Pacific",
  "timezone": "AEST (UTC+10)",
  "language": ["English", "Mandarin"],
  "businessType": ["Real Estate", "Commercial Development"],
  "projectPreferences": {
    "style": ["Modern", "Commercial"],
    "budget": "$200,000 - $500,000",
    "timeline": "3-6 months",
    "communication": ["Email", "Video Call"]
  },
  "projectHistory": {
    "total": 8,
    "completed": 6,
    "ongoing": 2,
    "value": 1850000
  },
  "paymentInfo": {
    "terms": "Net 30",
    "method": "Wire Transfer",
    "currency": "AUD",
    "creditRating": "A"
  },
  "bankInfo": {
    "beneficiaryBankName": "Commonwealth Bank of Australia",
    "beneficiaryBankAddress": "Sydney, NSW 2000, Australia",
    "beneficiaryBankCode": "062000",
    "swiftCode": "CTBAAU2S",
    "beneficiaryAccountName": "URBIS PTY LTD",
    "beneficiaryAccountNumber": "1234567890"
  },
  "tags": ["VIP客户", "长期合作"],
  "notes": "重要客户备注",
  "status": "active",
  "createdAt": "2024-01-01T00:00:00Z",
  "lastContact": "2025-01-26T15:30:00Z"
}
```

#### POST /api/clients
创建客户

#### GET /api/clients/{id}
获取客户详情

#### PUT /api/clients/{id}
更新客户信息

#### DELETE /api/clients/{id}
删除客户

### 4.2 客户数据导入导出

#### POST /api/clients/import
批量导入客户（Excel）

#### GET /api/clients/export
导出客户数据

#### GET /api/clients/template
下载客户信息模板

### 4.3 客户项目关联

#### GET /api/clients/{id}/projects
获取客户相关项目

#### PUT /api/clients/{id}/project-history
自动更新客户项目历史

## 5. 团队管理模块

### 5.1 团队成员管理

#### GET /api/team/members
获取团队成员列表
```json
{
  "code": 200,
  "data": [
    {
      "id": "TM001",
      "name": "张建模",
      "department": "modeling",
      "phone": "138****1234",
      "idCard": "310***********1234",
      "unitPrice": 800,
      "priceType": "fixed",
      "birdViewPrice": 1000,
      "humanViewPrice": 1200,
      "animationPrice": 1500,
      "customPrice": 1000,
      "bankInfo": "工商银行 6222***********1234",
      "paymentCycle": 30,
      "skills": ["3D Max", "Maya", "SketchUp", "Rhino"],
      "joinDate": "2023-01-15",
      "status": "active",
      "currentProjects": [
        {
          "projectId": "NF0810",
          "projectName": "Warsan Logistics Park R2",
          "dailyWorkload": 1
        }
      ]
    }
  ]
}
```

#### POST /api/team/members
添加团队成员

#### PUT /api/team/members/{id}
更新成员信息

#### DELETE /api/team/members/{id}
删除团队成员

### 5.2 工作量管理

#### GET /api/team/workload
获取团队工作量统计

#### PUT /api/team/members/{id}/workload
分配项目工作量

### 5.3 薪酬管理

#### GET /api/team/payments
获取薪资支付记录
```json
// 查询参数
{
  "month": "2025-01",
  "department": "modeling",
  "status": "pending"
}
```

#### POST /api/team/payments/calculate
计算月度薪资

#### PUT /api/team/payments/{id}/status
更新支付状态

#### GET /api/team/payments/history
获取历史支付记录

## 6. 财务管理模块

### 6.1 财务概览

#### GET /api/finance/overview
获取财务概览数据
```json
{
  "code": 200,
  "data": {
    "period": "2025-01",
    "revenue": {
      "total": 850000,
      "completed": 650000,
      "pending": 200000
    },
    "costs": {
      "projectManager": 17000,
      "modeling": 25000,
      "rendering": 35000,
      "sales": 8500,
      "fixed": 95000,
      "total": 180500
    },
    "profit": {
      "gross": 669500,
      "margin": 78.8
    },
    "projects": {
      "total": 15,
      "completed": 8,
      "ongoing": 7
    }
  }
}
```

### 6.2 收入管理

#### GET /api/finance/revenue
获取收入明细

#### PUT /api/finance/projects/{id}/payment
更新项目付款状态

### 6.3 成本管理

#### GET /api/finance/costs
获取成本结构

#### POST /api/finance/costs/fixed
录入固定成本

#### PUT /api/finance/costs/fixed/{id}
更新固定成本

### 6.4 账期管理

#### GET /api/finance/receivables
获取应收账款明细

#### PUT /api/finance/receivables/{id}/reminder
发送付款提醒

### 6.5 财务报表

#### GET /api/finance/reports/profit-loss
利润表

#### GET /api/finance/reports/cash-flow
现金流量表

#### POST /api/finance/reports/export
导出财务报表

## 7. 系统设置模块

### 7.1 系统配置

#### GET /api/settings/system
获取系统配置

#### PUT /api/settings/system
更新系统配置

### 7.2 汇率管理

#### GET /api/settings/exchange-rates
获取汇率配置
```json
{
  "code": 200,
  "data": {
    "baseCurrency": "CNY",
    "rates": {
      "USD": 7.24,
      "EUR": 7.85,
      "AUD": 4.78,
      "CAD": 5.32,
      "GBP": 9.12,
      "SGD": 5.36,
      "AED": 1.97
    },
    "lastUpdated": "2025-01-27T10:00:00Z"
  }
}
```

#### PUT /api/settings/exchange-rates
更新汇率

#### POST /api/settings/exchange-rates/sync
同步实时汇率

### 7.3 业务配置

#### GET /api/settings/business
获取业务配置（项目类型、服务类型等）

#### PUT /api/settings/business
更新业务配置

## 8. 数据统计与报表

### 8.1 仪表板数据

#### GET /api/dashboard/stats
获取仪表板统计数据
```json
{
  "code": 200,
  "data": {
    "projects": {
      "total": 40,
      "growth": 12
    },
    "revenue": {
      "monthly": 600000,
      "growth": 15
    },
    "team": {
      "members": 23,
      "workload": 80
    },
    "successRate": 95.5,
    "projectStatus": [
      {"name": "报备中", "value": 8},
      {"name": "建模中", "value": 15},
      {"name": "渲染中", "value": 12},
      {"name": "交付中", "value": 5}
    ],
    "monthlyTrend": [
      {"month": "2024-07", "revenue": 320000, "projects": 15},
      {"month": "2024-08", "revenue": 280000, "projects": 12}
    ]
  }
}
```

### 8.2 数据导出

#### GET /api/reports/projects/export
导出项目报表

#### GET /api/reports/clients/export
导出客户报表

#### GET /api/reports/finance/export
导出财务报表

## 9. 文件管理

### 9.1 文件上传

#### POST /api/files/upload
上传文件（支持图片、文档等）

#### GET /api/files/{id}
获取文件信息

#### DELETE /api/files/{id}
删除文件

### 9.2 PDF生成

#### POST /api/pdf/contract
生成合同PDF

#### POST /api/pdf/report
生成报表PDF

## 10. 通知系统

### 10.1 系统通知

#### GET /api/notifications
获取通知列表

#### PUT /api/notifications/{id}/read
标记通知已读

#### POST /api/notifications/send
发送通知

## 11. 数据库设计要点

### 11.1 核心表结构

#### 用户表 (users)
- id, username, password_hash, name, email, role, department, status, created_at, updated_at

#### 项目表 (projects)
- id, protocol_number, name, client_id, status, deadline, budget, currency, exchange_rate, progress, created_at, updated_at

#### 客户表 (clients)
- id, company_name, contact_person, email, phone, region, status, created_at, updated_at

#### 团队成员表 (team_members)
- id, name, department, phone, unit_price, price_type, skills, join_date, status

#### 财务记录表 (finance_records)
- id, project_id, type, amount, currency, status, created_at

### 11.2 关键索引
- projects: client_id, status, deadline
- finance_records: project_id, type, created_at
- clients: region, status
- team_members: department, status

## 12. 安全与性能要求

### 12.1 安全要求
- JWT Token 认证，过期时间24小时
- 敏感数据加密存储
- API 访问频率限制
- 权限验证中间件

### 12.2 性能要求
- 接口响应时间 < 500ms
- 支持分页查询
- 数据缓存策略
- 文件上传大小限制 50MB

## 13. 接口测试要求

### 13.1 单元测试
- 所有 CRUD 接口
- 权限验证逻辑
- 数据验证规则

### 13.2 集成测试
- 完整业务流程测试
- 第三方接口集成测试

## 14. 部署与运维

### 14.1 环境要求
- Node.js/Python/Java 后端框架
- MySQL/PostgreSQL 数据库
- Redis 缓存
- Nginx 反向代理

### 14.2 监控要求
- API 响应时间监控
- 错误日志记录
- 系统资源监控

---

**文档版本**: v1.0  
**最后更新**: 2025-01-27  
**维护人员**: NFLAB 开发团队 