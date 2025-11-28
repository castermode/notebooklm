import subprocess
import time
import asyncio
from playwright.async_api import async_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_PATH = "/Users/mhlee/tmp/chrome-profile-9922"
PORT = 9922

def start_chrome():
    print(f"启动 Chrome，端口：{PORT}")
    command = (
        f'"{CHROME_PATH}" '
        f'--remote-debugging-port={PORT} '
        f'--user-data-dir="{PROFILE_PATH}" '
        f'--remote-allow-origins=* '
        f'--disable-download-restrictions'
    )
    subprocess.Popen(command, shell=True)
    time.sleep(3)
    print(f"Chrome 已启动，端口：{PORT}")


async def new_notebook(driver, file_path='/Users/mhlee/Work/ke/notebooklm/data/KeMemDesign.pdf', convert_file_type = 'Audio Overview'):

    await driver.get_by_role("button", name="Create new notebook").nth(0).click()

    # 如果需要点击 span 按钮（可选）
    # driver.get_by_role("button", name="选择文件").click()
    await asyncio.sleep(3)

    await driver.locator('input[name="Filedata"]').set_input_files(file_path, timeout=0)

    await asyncio.sleep(2)

    # 等待上传完毕
    # 等待按钮出现（最长等 30 秒）
    audio_button = driver.get_by_role("button", name=convert_file_type).nth(0)
    await audio_button.wait_for(state="visible", timeout=30000)

    # 等待按钮可用（不是 disabled）
    for _ in range(30):  # 最多等 30 秒
        if not await audio_button.is_disabled():
            await audio_button.click()
            print("按钮已点击")
            break
        else:
            await driver.wait_for_timeout(1000)  # 等 1 秒再检查
    else:
        print("按钮在超时时间内一直是禁用状态")
    print("等待更多按钮出现...")

    for i in range(30):  # 最多检查 10 次
        if await driver.locator('button[aria-label="More"].artifact-more-button').count() > 0:

            await driver.locator('button[aria-label="More"].artifact-more-button').nth(0).click()
            print("已点击更多按钮")
            break
        else:
            print(f"第 {i + 1} 次检查：按钮未出现，等待 30 秒")
            await asyncio.sleep(30)

    # more_button = driver.get_by_role("button", name="更多")
    # more_button.wait_for(state="visible", timeout=1200000)  # 最长等 10 分钟
    # more_button = driver.wait_for_selector('button[aria-label="更多"]', state="attached", timeout=1200000)
    # more_button.click()

    await driver.get_by_role("menuitem", name="Download").click()


async def connect_and_open():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(f"http://localhost:{PORT}")

        # ⭐ 使用 Chrome 自带的 context，不要 new_context()
        context = browser.contexts[0]

        # 当前 Chrome 已打开的标签
        page = context.pages[0]

        print("接管页面成功：", page.url)

        # ⭐ 监听下载事件并手动保存文件
        async def on_download(download):
            save_path = "/Users/mhlee/Work/ke/notebooklm/downloads/" + download.suggested_filename
            print(f"保存文件 -> {save_path}")
            await download.save_as(save_path)

        page.on("download", on_download)

        # await page.goto("https://notebooklm.google.com/?icid=home_maincta&_gl=1*1rzjuad*_ga*ODYxMjgzODE0LjE3NjQyNDMyNjI.*_ga_W0LDH41ZCB*czE3NjQyNDMyNjEkbzEkZzAkdDE3NjQyNDMyNjEkajYwJGwwJGgw&original_referer=https:%2F%2Fnotebooklm.google%23&pli=1")
        await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")

        await new_notebook(page)

        #保持运行
        while True:
            await asyncio.sleep(1)

def main():
    start_chrome()
    asyncio.run(connect_and_open())

if __name__ == "__main__":
    main()
