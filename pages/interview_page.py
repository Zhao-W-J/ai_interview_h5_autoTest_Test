import re
import random

class InterviewPage:

    def __init__(self, page):
        self.page = page

    async def start_interview(self):
        """开始面试"""
        await self.page.get_by_role(
            "button",
            name="我已知晓，开始面试"
        ).click()

        await self.page.get_by_role(
            "button",
            name="确认开始"
        ).click()

    async def answer_question(self):
        """回答题目"""
        # 等待按钮出现（增加超时时间）
        button = self.page.locator(
            "div"
        ).filter(
            has_text=re.compile(r"^点击开始录音|^请点击录制开始录制$")
        ).get_by_role(
            "button"
        )

        await button.wait_for(timeout=35000)
        await button.click()

        # 答题录音：30 秒 -10 分钟随机
        random_time = random.randint(30000, 600000)
        await self.page.wait_for_timeout(random_time)

        # 完成按钮
        done_button = self.page.locator(
            "div"
        ).filter(
            has_text=re.compile(r"^完成本题$")
        ).get_by_role(
            "button"
        )

        await done_button.wait_for(timeout=10000)
        await done_button.click()

        # 确认按钮
        try:
            await self.page.get_by_role(
                "button",
                name="确定"
            ).click(timeout=5000)
        except:
            pass  # 没有确认按钮也继续
