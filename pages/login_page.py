class LoginPage:

    def __init__(self, page):
        self.page = page

    async def login(self, code="0126"):
        for i, num in enumerate(code):
            await self.page.get_by_role(
                "textbox"
            ).nth(i).fill(num)

        await self.page.get_by_role(
            "button",
            name="登录"
        ).click()