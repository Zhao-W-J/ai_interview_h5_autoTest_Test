import re

class InterviewPage:

    def __init__(self, page):
        self.page = page

    def start_interview(self):

        self.page.get_by_role(
            "button",
            name="我已知晓，开始面试"
        ).click()

        self.page.get_by_role(
            "button",
            name="确认开始"
        ).click()

    def answer_question(self):

        self.page.locator(
            "div"
        ).filter(
            has_text=re.compile(r"^请点击录制开始录制$")
        ).get_by_role(
            "button"
        ).click()

        self.page.wait_for_timeout(50000)

        self.page.locator(
            "div"
        ).filter(
            has_text=re.compile(r"^完成本题$")
        ).get_by_role(
            "button"
        ).click()

        self.page.get_by_role(
            "button",
            name="确定"
        ).click()