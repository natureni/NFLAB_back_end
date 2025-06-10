#!/usr/bin/env python3

import requests
import json

def test_comprehensive_api():
    """全面测试API和前端连接问题"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 开始全面API测试...")
    
    # 1. 登录获取token
    try:
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        login_response.raise_for_status()
        token = login_response.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print("✅ 登录成功")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
        
    # 2. 测试客户API
    print("\n📋 测试客户相关API...")
    client_endpoints = [
        ("GET", "/api/clients", "客户列表"),
        ("GET", "/api/clients/statistics", "客户统计"),
        ("GET", "/api/clients/template", "客户模板"),
    ]
    
    for method, endpoint, desc in client_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"{method} {endpoint} ({desc}) - 状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if endpoint == "/api/clients":
                    print(f"   ✅ 成功: 共 {data['data']['total']} 个客户")
                    for client in data['data']['list'][:3]:  # 显示前3个
                        print(f"      - {client['company_name']} ({client['region']})")
                elif endpoint == "/api/clients/statistics":
                    stats = data['data']
                    print(f"   ✅ 成功: 总客户 {stats['total_clients']}, 活跃 {stats['active_clients']}")
                elif endpoint == "/api/clients/template":
                    print(f"   ✅ 成功: 模板包含 {len(data['data']['required_fields'])} 个必填字段")
            else:
                print(f"   ❌ 失败: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 3. 测试项目API (解决403问题)
    print("\n🏗️ 测试项目相关API...")
    project_endpoints = [
        ("GET", "/api/projects", "项目列表"),
        ("GET", "/api/projects/services/templates", "服务模板"),
    ]
    
    for method, endpoint, desc in project_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"{method} {endpoint} ({desc}) - 状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if endpoint == "/api/projects":
                    print(f"   ✅ 成功: 共 {data['data']['total']} 个项目")
                    for project in data['data']['list'][:3]:  # 显示前3个
                        print(f"      - {project['name']} ({project['status']}, {project['progress']}%)")
                elif endpoint == "/api/projects/services/templates":
                    templates = data['data']
                    print(f"   ✅ 成功: 共 {len(templates)} 个服务模板")
            elif response.status_code == 403:
                print(f"   ❌ 403 Forbidden - 权限问题")
                print(f"      可能原因: 1) Token过期 2) 权限不足 3) CORS问题")
                print(f"      Token格式: {headers['Authorization'][:20]}...")
                print(f"      响应详情: {response.text}")
            else:
                print(f"   ❌ 状态码 {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 4. 测试团队API
    print("\n👥 测试团队相关API...")
    team_endpoints = [
        ("GET", "/api/team", "团队成员列表"),
    ]
    
    for method, endpoint, desc in team_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"{method} {endpoint} ({desc}) - 状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    if isinstance(data['data'], list):
                        print(f"   ✅ 成功: 共 {len(data['data'])} 个团队成员")
                        for member in data['data'][:3]:  # 显示前3个
                            print(f"      - {member['name']} ({member['department']}, ¥{member['unit_price']}/小时)")
                    else:
                        print(f"   ✅ 成功: {data['data']}")
                else:
                    print(f"   ✅ 成功: {len(data)} 个团队成员")
            else:
                print(f"   ❌ 状态码 {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 5. 测试仪表板API
    print("\n📊 测试仪表板相关API...")
    dashboard_endpoints = [
        ("GET", "/api/dashboard/stats", "仪表板统计"),
    ]
    
    for method, endpoint, desc in dashboard_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"{method} {endpoint} ({desc}) - 状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                stats = data['data']
                print(f"   ✅ 成功: 仪表板数据完整")
                print(f"      - 项目状态: {len(stats.get('project_status', []))} 个状态")
                print(f"      - 月度收入: {len(stats.get('monthly_revenue', []))} 个月份")
                print(f"      - 团队工作量: {len(stats.get('team_workload', []))} 个成员")
            else:
                print(f"   ❌ 状态码 {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 6. 测试CORS预检请求 (OPTIONS)
    print("\n🌐 测试CORS预检请求...")
    try:
        options_response = requests.options(
            f"{base_url}/api/projects",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            }
        )
        print(f"OPTIONS /api/projects - 状态码: {options_response.status_code}")
        if options_response.status_code in [200, 204]:
            print("   ✅ CORS预检成功")
            cors_headers = {k: v for k, v in options_response.headers.items() if k.lower().startswith('access-control')}
            for header, value in cors_headers.items():
                print(f"      {header}: {value}")
        else:
            print(f"   ❌ CORS预检失败: {options_response.text}")
    except Exception as e:
        print(f"   ❌ CORS测试异常: {e}")
    
    print("\n🎯 测试总结:")
    print("如果项目API返回403错误，可能的解决方案:")
    print("1. 检查前端是否正确发送Authorization header")
    print("2. 确认token格式正确 (Bearer <token>)")
    print("3. 检查CORS配置是否允许localhost:3000")
    print("4. 确认前端发送的请求URL正确")
    print("5. 检查后端项目API的权限配置")

if __name__ == "__main__":
    test_comprehensive_api() 