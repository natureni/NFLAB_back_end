#!/usr/bin/env python3
"""
NFLAB项目管理系统 - 完整系统功能测试
测试所有已实现的模块：认证、项目、客户、团队、设置、财务、文件、通知、权限、报表
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date
from typing import Dict, Any

# API基础配置
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

class NFLABCompleteSystemTest:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {status} {test_name}")
        if details:
            print(f"    详情: {details}")
    
    async def authenticate(self):
        """用户认证"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/auth/login",
                data=login_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result["access_token"]
                    self.headers = {
                        **HEADERS,
                        "Authorization": f"Bearer {self.auth_token}"
                    }
                    self.log_test("用户认证", True, f"获取到访问令牌")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("用户认证", False, f"状态码: {response.status}, 错误: {error_text}")
                    return False
        except Exception as e:
            self.log_test("用户认证", False, f"异常: {str(e)}")
            return False
    
    async def test_basic_modules(self):
        """测试基础模块（认证、项目、客户、仪表板）"""
        print("\n=== 基础模块测试 ===")
        
        # 1. 获取项目列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/projects",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    total_projects = result["total"]
                    self.log_test("获取项目列表", True, f"共 {total_projects} 个项目")
                else:
                    error_text = await response.text()
                    self.log_test("获取项目列表", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取项目列表", False, f"异常: {str(e)}")
        
        # 2. 获取客户列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/clients",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    total_clients = result["total"]
                    self.log_test("获取客户列表", True, f"共 {total_clients} 个客户")
                else:
                    error_text = await response.text()
                    self.log_test("获取客户列表", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取客户列表", False, f"异常: {str(e)}")
        
        # 3. 获取仪表板数据
        try:
            async with self.session.get(
                f"{BASE_URL}/api/dashboard/stats",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    total_revenue = stats["total_revenue"]
                    self.log_test("获取仪表板数据", True, f"总收入: ¥{total_revenue:,.2f}")
                else:
                    error_text = await response.text()
                    self.log_test("获取仪表板数据", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取仪表板数据", False, f"异常: {str(e)}")
    
    async def test_team_management(self):
        """测试团队管理模块"""
        print("\n=== 团队管理模块测试 ===")
        
        # 1. 获取团队成员列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/team/members",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    total_members = result["total"]
                    self.log_test("获取团队成员列表", True, f"共 {total_members} 名成员")
                else:
                    error_text = await response.text()
                    self.log_test("获取团队成员列表", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取团队成员列表", False, f"异常: {str(e)}")
        
        # 2. 获取工作量统计
        try:
            async with self.session.get(
                f"{BASE_URL}/api/team/workload",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    workload_data = await response.json()
                    self.log_test("获取工作量统计", True, f"获取到 {len(workload_data)} 名成员的工作量数据")
                else:
                    error_text = await response.text()
                    self.log_test("获取工作量统计", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取工作量统计", False, f"异常: {str(e)}")
        
        # 3. 计算月度薪资
        try:
            current_date = datetime.now()
            async with self.session.post(
                f"{BASE_URL}/api/team/payments/calculate?year={current_date.year}&month={current_date.month}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    salary_data = await response.json()
                    total_amount = salary_data["total_amount"]
                    self.log_test("计算月度薪资", True, f"总薪资: ¥{total_amount:,.2f}")
                else:
                    error_text = await response.text()
                    self.log_test("计算月度薪资", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("计算月度薪资", False, f"异常: {str(e)}")
    
    async def test_settings_management(self):
        """测试系统设置模块"""
        print("\n=== 系统设置模块测试 ===")
        
        # 1. 获取系统配置
        try:
            async with self.session.get(
                f"{BASE_URL}/api/settings/system",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    config = await response.json()
                    app_name = config["app_name"]
                    self.log_test("获取系统配置", True, f"应用名称: {app_name}")
                else:
                    error_text = await response.text()
                    self.log_test("获取系统配置", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取系统配置", False, f"异常: {str(e)}")
        
        # 2. 获取汇率配置
        try:
            async with self.session.get(
                f"{BASE_URL}/api/settings/exchange-rates",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    rates = await response.json()
                    cny_rate = rates["rates"].get("cny", 0)
                    self.log_test("获取汇率配置", True, f"人民币汇率: {cny_rate}")
                else:
                    error_text = await response.text()
                    self.log_test("获取汇率配置", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取汇率配置", False, f"异常: {str(e)}")
        
        # 3. 获取业务配置
        try:
            async with self.session.get(
                f"{BASE_URL}/api/settings/business",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    config = await response.json()
                    default_currency = config["default_currency"]
                    self.log_test("获取业务配置", True, f"默认货币: {default_currency}")
                else:
                    error_text = await response.text()
                    self.log_test("获取业务配置", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取业务配置", False, f"异常: {str(e)}")
    
    async def test_finance_management(self):
        """测试财务管理模块"""
        print("\n=== 财务管理模块测试 ===")
        
        # 1. 获取财务概览
        try:
            async with self.session.get(
                f"{BASE_URL}/api/finance/overview",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    overview = await response.json()
                    total_revenue = overview["total_revenue"]
                    net_profit = overview["net_profit"]
                    self.log_test("获取财务概览", True, f"总收入: ¥{total_revenue:,.2f}, 净利润: ¥{net_profit:,.2f}")
                else:
                    error_text = await response.text()
                    self.log_test("获取财务概览", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取财务概览", False, f"异常: {str(e)}")
        
        # 2. 获取收入明细
        try:
            async with self.session.get(
                f"{BASE_URL}/api/finance/revenue",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    total_records = result["total"]
                    self.log_test("获取收入明细", True, f"共 {total_records} 条收入记录")
                else:
                    error_text = await response.text()
                    self.log_test("获取收入明细", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取收入明细", False, f"异常: {str(e)}")
        
        # 3. 获取应收账款
        try:
            async with self.session.get(
                f"{BASE_URL}/api/finance/receivables",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    receivables = await response.json()
                    self.log_test("获取应收账款", True, f"共 {len(receivables)} 笔应收账款")
                else:
                    error_text = await response.text()
                    self.log_test("获取应收账款", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取应收账款", False, f"异常: {str(e)}")
    
    async def test_file_management(self):
        """测试文件管理模块"""
        print("\n=== 文件管理模块测试 ===")
        
        # 1. 获取文件列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/files/",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    files = await response.json()
                    self.log_test("获取文件列表", True, f"共 {len(files)} 个文件")
                else:
                    error_text = await response.text()
                    self.log_test("获取文件列表", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取文件列表", False, f"异常: {str(e)}")
        
        # 2. 获取存储统计
        try:
            async with self.session.get(
                f"{BASE_URL}/api/files/storage/stats",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    total_files = stats["total_files"]
                    total_size_mb = stats["total_size_mb"]
                    self.log_test("获取存储统计", True, f"文件数: {total_files}, 总大小: {total_size_mb}MB")
                else:
                    error_text = await response.text()
                    self.log_test("获取存储统计", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取存储统计", False, f"异常: {str(e)}")
    
    async def test_notifications(self):
        """测试通知系统模块"""
        print("\n=== 通知系统模块测试 ===")
        
        # 1. 获取通知列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/notifications/",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    total_notifications = result["total"]
                    unread_count = result["unread_count"]
                    self.log_test("获取通知列表", True, f"总通知: {total_notifications}, 未读: {unread_count}")
                else:
                    error_text = await response.text()
                    self.log_test("获取通知列表", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取通知列表", False, f"异常: {str(e)}")
        
        # 2. 获取通知统计
        try:
            async with self.session.get(
                f"{BASE_URL}/api/notifications/stats",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    urgent_count = stats["urgent_count"]
                    today_count = stats["today_count"]
                    self.log_test("获取通知统计", True, f"紧急通知: {urgent_count}, 今日通知: {today_count}")
                else:
                    error_text = await response.text()
                    self.log_test("获取通知统计", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取通知统计", False, f"异常: {str(e)}")
        
        # 3. 发送通知（仅管理员）
        notification_data = {
            "title": "系统测试通知",
            "content": "这是一个自动化测试发送的通知消息",
            "type": "system_alert",
            "priority": "medium"
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/notifications/send",
                headers=self.headers,
                json=notification_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.log_test("发送通知", True, f"发送成功: {result['message']}")
                else:
                    error_text = await response.text()
                    self.log_test("发送通知", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("发送通知", False, f"异常: {str(e)}")
    
    async def test_permissions(self):
        """测试权限管理模块"""
        print("\n=== 权限管理模块测试 ===")
        
        # 1. 获取角色权限配置
        try:
            async with self.session.get(
                f"{BASE_URL}/api/permissions/roles",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    roles = await response.json()
                    self.log_test("获取角色权限配置", True, f"共 {len(roles)} 个角色")
                else:
                    error_text = await response.text()
                    self.log_test("获取角色权限配置", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取角色权限配置", False, f"异常: {str(e)}")
        
        # 2. 获取权限矩阵
        try:
            async with self.session.get(
                f"{BASE_URL}/api/permissions/matrix",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    matrix = await response.json()
                    permissions_count = len(matrix["permissions"])
                    roles_count = len(matrix["roles"])
                    self.log_test("获取权限矩阵", True, f"权限数: {permissions_count}, 角色数: {roles_count}")
                else:
                    error_text = await response.text()
                    self.log_test("获取权限矩阵", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取权限矩阵", False, f"异常: {str(e)}")
        
        # 3. 获取当前用户权限
        try:
            async with self.session.get(
                f"{BASE_URL}/api/permissions/user/permissions",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    permissions = await response.json()
                    self.log_test("获取当前用户权限", True, f"拥有 {len(permissions)} 个权限")
                else:
                    error_text = await response.text()
                    self.log_test("获取当前用户权限", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取当前用户权限", False, f"异常: {str(e)}")
    
    async def test_reports(self):
        """测试报表导出模块"""
        print("\n=== 报表导出模块测试 ===")
        
        # 1. 导出项目报表
        export_request = {
            "report_type": "projects",
            "format": "excel",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "include_details": True
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/reports/export",
                headers=self.headers,
                json=export_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    task_id = result["task_id"]
                    self.log_test("导出项目报表", True, f"任务ID: {task_id[:8]}...")
                    
                    # 检查导出状态
                    await asyncio.sleep(2)  # 等待处理
                    async with self.session.get(
                        f"{BASE_URL}/api/reports/export/{task_id}/status",
                        headers=self.headers
                    ) as status_response:
                        if status_response.status == 200:
                            status_result = await status_response.json()
                            task_status = status_result["status"]
                            self.log_test("检查导出状态", True, f"任务状态: {task_status}")
                        else:
                            self.log_test("检查导出状态", False, f"状态码: {status_response.status}")
                else:
                    error_text = await response.text()
                    self.log_test("导出项目报表", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("导出项目报表", False, f"异常: {str(e)}")
        
        # 2. 获取导出任务列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/reports/tasks",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    tasks = await response.json()
                    self.log_test("获取导出任务列表", True, f"共 {len(tasks)} 个任务")
                else:
                    error_text = await response.text()
                    self.log_test("获取导出任务列表", False, f"状态码: {response.status}")
        except Exception as e:
            self.log_test("获取导出任务列表", False, f"异常: {str(e)}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始NFLAB项目管理系统完整功能测试")
        print("=" * 60)
        
        # 认证
        if not await self.authenticate():
            print("❌ 认证失败，无法继续测试")
            return
        
        # 运行各模块测试
        await self.test_basic_modules()
        await self.test_team_management()
        await self.test_settings_management()
        await self.test_finance_management()
        await self.test_file_management()
        await self.test_notifications()
        await self.test_permissions()
        await self.test_reports()
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 系统完整性测试结果统计")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n🎉 NFLAB项目管理系统完整功能测试完成！")
        print(f"✨ 系统覆盖模块: 认证、项目、客户、团队、设置、财务、文件、通知、权限、报表")
        print(f"📈 系统完整度: {success_rate:.1f}%")

async def main():
    """主函数"""
    async with NFLABCompleteSystemTest() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 