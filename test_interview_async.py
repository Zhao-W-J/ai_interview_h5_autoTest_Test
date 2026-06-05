from playwright.async_api import async_playwright
from pages.login_page import LoginPage
from pages.verify_page import VerifyPage
from pages.interview_page import InterviewPage
from network_sniffer import NetworkSniffer

import asyncio
import os
import pymysql
from db_config import DB_CONFIG, TABLE_NAME, QUESTION_TABLE_NAME, STATIC_CONDITIONS, EXCLUDE_NAMES, END_TIME_FIELD, BASE_URL

# 创建数据库连接
def get_interviewees(limit=100):
    """从数据库获取面试者信息"""
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset="utf8mb4"
    )

    cursor = conn.cursor()

    # 构建静态查询条件（加表别名 r. 避免歧义）
    conditions = " AND ".join([f"r.{k} = {v}" for k, v in STATIC_CONDITIONS.items()])

    # 构建排除条件（排除张三等名字）
    if EXCLUDE_NAMES:
        exclude_list = "', '".join(EXCLUDE_NAMES)
        exclude_condition = f"AND r.name NOT IN ('{exclude_list}')"
    else:
        exclude_condition = ""

    # 构建动态日期条件
    date_condition = ""
    if END_TIME_FIELD:
        date_condition = f"AND r.{END_TIME_FIELD} > CURDATE()"

    # 查询 token, phone 和题目数量
    sql = f"""
        SELECT r.token, r.phone, COUNT(q.id) as question_count
        FROM {TABLE_NAME} r
        LEFT JOIN {QUESTION_TABLE_NAME} q ON r.token = q.token
        WHERE {conditions}
        {exclude_condition}
        {date_condition}
        GROUP BY r.token, r.phone
        ORDER BY r.token ASC
        LIMIT %s
    """

    cursor.execute(sql, (limit,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    # 返回 (token, 手机尾号，题目数量) 列表
    interviewees = []
    for token, phone, question_count in results:
        phone_tail = str(phone)[-4:]  # 取后 4 位
        interviewees.append((token, phone_tail, question_count))

    return interviewees


os.makedirs("logs", exist_ok=True)
os.makedirs("videos", exist_ok=True)
os.makedirs("traces", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

# 并发数限制
MAX_CONCURRENCY = 5

# Xiaomi 13 Pro 配置
VIVO_X70 = {
    "viewport": {"width": 393, "height": 873},
    "user_agent": "Mozilla/5.0 (Linux; Android 13; 2210132C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "device_scale_factor": 3,
    "is_mobile": True,
    "has_touch": True,
}


async def run_interview(browser, token, phone_tail, question_count, semaphore, index):
    """执行单个面试流程"""
    async with semaphore:
        print(f"\n===== 第 {index+1} 位面试者：尾号 {phone_tail}，共 {question_count} 题 =====")

        url = f"{BASE_URL}{token}"
        print(f"URL: {url}")

        context = await browser.new_context(
            **VIVO_X70,
            ignore_https_errors=True,
        )

        await context.grant_permissions(
            ["microphone"],
            origin="https://116.30.7.119:57070"
        )

        context.tracing.start(
            screenshots=True,
            snapshots=True
        )

        page = await context.new_page()

        # 网络抓包
        sniffer = NetworkSniffer(
            page,
            log_dir="logs",
        )

        sniffer.start()
        page.set_default_timeout(50000)

        try:
            # 打开页面
            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            # 页面对象
            login_page = LoginPage(page)
            verify_page = VerifyPage(page)
            interview_page = InterviewPage(page)

            # 登录
            await login_page.login(phone_tail)

            # 验证
            await verify_page.start_verify()
            await verify_page.voice_verify()

            # 开始面试
            await interview_page.start_interview()

            # 答题
            for j in range(question_count):
                print(f"  回答第 {j+1} 题...")
                await interview_page.answer_question()
                print(f"  第 {j+1} 题完成")

            print("  等待面试结束页面...")
            await page.wait_for_selector("text=面试已圆满结束", timeout=70000)

            print(f"第 {index+1} 位面试者测试成功")

        except Exception as e:
            print(f"第 {index+1} 位面试者测试失败")
            print(e)

            # 保存失败截图
            await page.screenshot(
                path=f"screenshots/fail_{index+1}_{phone_tail}.png",
                full_page=True
            )

        # 停止抓包
        sniffer.stop()

        # 关闭当前 context
        await context.close()


async def main():
    # 获取所有面试者信息
    interviewees = get_interviewees()

    if not interviewees:
        print("未找到符合条件的面试者数据！")
        return

    print(f"找到 {len(interviewees)} 位面试者")
    print(f"最大并发数：{MAX_CONCURRENCY}")

    # 创建信号量控制并发
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async with async_playwright() as p:
        import os
        is_docker = os.getenv('IS_DOCKER', 'false').lower() == 'true'

        # 启动浏览器
        browser = await p.chromium.launch(
            headless=is_docker,  # Docker 环境 headless=True，本地 headless=False
            slow_mo=300,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                r"--use-file-for-fake-video-capture=C:\Users\zwj\daima\ai_interview_h5_autoTest\wav\face.y4m",
                r"--use-file-for-fake-audio-capture=C:\Users\zwj\daima\ai_interview_h5_autoTest\wav\ready.wav",
            ]
        )

        # 创建所有任务
        tasks = []
        for i, (token, phone_tail, question_count) in enumerate(interviewees):
            task = run_interview(browser, token, phone_tail, question_count, semaphore, i)
            tasks.append(task)

        # 并行执行（受 semaphore 限制）
        await asyncio.gather(*tasks)

        # 所有任务完成后关闭浏览器
        # await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
