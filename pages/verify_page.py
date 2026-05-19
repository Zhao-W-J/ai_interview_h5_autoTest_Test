import re

class VerifyPage:

    def __init__(self, page):
        self.page = page

    def start_verify(self):

        self.page.get_by_role(
            "button",
            name="开始验证"
        ).click()

    def voice_verify(self):

        # 点击开始录音
        self.page.locator("div").filter(
            has_text=re.compile(r"^点击开始录音$")
        ).get_by_role("button").click()

        # 等待录音完成（说"我已做好准备"）
        self.page.wait_for_timeout(5000)

        # 点击停止录音按钮（用 force=True 绕过遮挡检查）
        self.page.locator(".voice-btn.listening").click(force=True)

        # 等待验证完成
        self.page.wait_for_timeout(3000)