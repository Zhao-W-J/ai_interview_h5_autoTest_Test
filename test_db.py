#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据库连接测试脚本"""
import pymysql
from db_config import DB_CONFIG

print("=" * 50)
print("数据库连接测试")
print("=" * 50)
print(f"Host: {DB_CONFIG.get('host')}")
print(f"User: {DB_CONFIG.get('user')}")
print(f"Database: {DB_CONFIG.get('database')}")
print("=" * 50)

try:
    connection = pymysql.connect(**DB_CONFIG)
    print("✅ 数据库连接成功!")

    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL 版本：{version[0]}")

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"表数量：{len(tables)}")
        print(f"表名：{[t[0] for t in tables]}")

    connection.close()
    print("✅ 测试完成!")

except Exception as e:
    print(f"❌ 连接失败：{e}")
