# -*- coding: utf-8 -*-
"""权限体系冒烟测试：注册已关闭 / 管理员建号 / 权限隔离 / 禁用 / 改密 / 重置密码"""
import httpx

B = "http://127.0.0.1:8002"
c = httpx.Client(base_url=B, timeout=30)
ok = True


def check(name, cond, extra=""):
    global ok
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {extra}")
    if not cond:
        ok = False


# 1. 注册接口已关闭
r = c.post("/api/auth/register", json={"username": "x", "password": "x123456"})
check("注册接口已关闭(404/405)", r.status_code in (404, 405), f"-> {r.status_code}")

# 2. demo(admin) 登录
r = c.post("/api/auth/login", json={"username": "demo", "password": "demo123456"})
check("demo 登录", r.status_code == 200)
check("demo 是管理员", r.json()["user"]["role"] == "admin")
admin = c  # 复用 client
admin.headers["Authorization"] = f"Bearer {r.json()['token']}"

# 3. 管理员创建普通用户
r = admin.post("/api/admin/users", json={"username": "alice", "password": "alice123456", "display_name": "爱丽丝", "role": "user"})
check("创建用户 alice", r.status_code == 200, f"-> {r.status_code} {r.json().get('detail','')}")
r = admin.post("/api/admin/users", json={"username": "alice", "password": "alice123456"})
check("重复用户名被拒", r.status_code == 400)

# 4. alice 登录
r = c.post("/api/auth/login", json={"username": "alice", "password": "alice123456"})
check("alice 登录", r.status_code == 200)
alice = httpx.Client(base_url=B, timeout=30)
alice.headers["Authorization"] = f"Bearer {r.json()['token']}"

# 5. alice 访问管理接口被拒
r = alice.get("/api/admin/users")
check("alice 访问用户管理被拒(403)", r.status_code == 403, f"-> {r.status_code}")
# 6. alice 可访问业务接口
r = alice.get("/api/vehicles")
check("alice 可访问业务接口", r.status_code == 200)

# 7. alice 改密
r = alice.put("/api/auth/change-password", json={"old_password": "alice123456", "new_password": "alice654321"})
check("alice 修改密码", r.status_code == 200)
r = c.post("/api/auth/login", json={"username": "alice", "password": "alice654321"})
check("alice 新密码登录", r.status_code == 200)

# 8. 管理员禁用 alice
r = admin.put("/api/admin/users/2", json={"is_active": False})
check("禁用 alice", r.status_code == 200)
r = c.post("/api/auth/login", json={"username": "alice", "password": "alice654321"})
check("禁用后 alice 无法登录(403)", r.status_code == 403, f"-> {r.status_code}")

# 9. 管理员重置密码并启用
r = admin.put("/api/admin/users/2", json={"is_active": True, "password": "reset123456"})
check("重置密码并启用", r.status_code == 200)
r = c.post("/api/auth/login", json={"username": "alice", "password": "reset123456"})
check("alice 用重置密码登录", r.status_code == 200)

# 10. 自我保护：admin 不能禁用自己
r = admin.put("/api/admin/users/1", json={"is_active": False})
check("管理员不能禁用自己(400)", r.status_code == 400, f"-> {r.status_code}")

# 11. 删除 alice（id=2）
r = admin.delete("/api/admin/users/2")
check("删除 alice", r.status_code == 200)
r = c.post("/api/auth/login", json={"username": "alice", "password": "reset123456"})
check("删除后 alice 无法登录", r.status_code == 401)

print("\nALL PASS" if ok else "\nSOME FAILED")
