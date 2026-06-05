from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from pages.verify_page import VerifyPage
from pages.interview_page import InterviewPage
from network_sniffer import NetworkSniffer

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

# 获取所有面试者信息
interviewees = get_interviewees()

if not interviewees:
    print("未找到符合条件的面试者数据！")
    exit(1)

print(f"找到 {len(interviewees)} 位面试者")

with sync_playwright() as p:

    # 只启动一次浏览器
    import os
    is_docker = os.getenv('IS_DOCKER', 'false').lower() == 'true'

    browser = p.chromium.launch(
        headless=is_docker,  # Docker 环境 headless=True，本地 headless=False
        slow_mo=100,
        args=[
            # 自动允许权限
            "--use-fake-ui-for-media-stream",
            # 使用 fake 设备（必须）
            "--use-fake-device-for-media-stream",
            # fake 视频
            r"--use-file-for-fake-video-capture=C:\Users\zwj\daima\ai_interview_h5_autoTest\wav\face.y4m",

            # fake 音频
            r"--use-file-for-fake-audio-capture=C:\Users\zwj\daima\ai_interview_h5_autoTest\wav\ready.wav",
        ]
    )

    # 自定义 Xiaomi 13 Pro 配置
    vivo_x70 = {
        "viewport": {"width": 393, "height": 873},
        "user_agent": "Mozilla/5.0 (Linux; Android 13; 2210132C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    }

    for i, (token, phone_tail, question_count) in enumerate(interviewees):

        print(f"\n===== 第 {i+1} 位面试者：尾号 {phone_tail}，共 {question_count} 题 =====")

        # 拼接动态 URL
        url = f"{BASE_URL}{token}"

        print(f"URL: {url}")

        # 每个面试者创建新的 context 和 page
        context = browser.new_context(
            **vivo_x70,

            ignore_https_errors=True,

            # 不保存视频
            # record_video_dir=f"videos/",
        )

        context.grant_permissions(
            ["microphone"],
            origin="https://116.30.7.119:57070"
        )

        # trace
        context.tracing.start(
            screenshots=True,
            snapshots=True
        )


        page = context.new_page()

        # 网络抓包
        sniffer = NetworkSniffer(
            page,
            log_dir="logs",
        )

        sniffer.start()
        # 设置全局默认超时
        page.set_default_timeout(30000)

        # 通过 CDP 模拟网络条件
        # client = context.new_cdp_session(page)
        # client.send("Network.enable")

        # client.send("Network.emulateNetworkConditions", {
        #     "offline": False,

        #     # 延迟（毫秒）
        #     "latency": 80,

        #     # 下载速度（字节/s）
        #     "downloadThroughput": 4 * 1024 * 1024 / 8,

        #     # 上传速度（字节/s）
        #     "uploadThroughput": 3 * 1024 * 1024 / 8,
        # })

        try:

            # 打开页面
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=80000 # 页面加载超时
            )

            # 页面对象
            login_page = LoginPage(page)

            verify_page = VerifyPage(page)

            interview_page = InterviewPage(page)

            # 登录（使用数据库中的手机尾号）
            login_page.login(phone_tail)

            # 验证
            verify_page.start_verify()

            verify_page.voice_verify()

            # 开始面试
            interview_page.start_interview()

            # 答题（动态题数）
            for j in range(question_count):
                print(f"  回答第 {j+1} 题...")
                interview_page.answer_question()
                print(f"  第 {j+1} 题完成")

            print("  等待面试结束页面...")
            # 等待面试结束页面出现
            page.wait_for_selector("text=面试已圆满结束", timeout=5000) #等待结束页面超时

            print(f"第 {i+1} 位面试者测试成功")

        except Exception as e:

            print(f"第 {i+1} 位面试者测试失败")
            print(e)

            # 保存失败截图
            page.screenshot(
                path=f"screenshots/fail_{i+1}_{phone_tail}.png",
                full_page=True
            )

        # 停止抓包
        sniffer.stop()

        # 关闭当前 context（保留浏览器）
        context.close()

    # 所有面试者测试完成后关闭浏览器
    # browser.close()
