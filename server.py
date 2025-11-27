from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import subprocess
import time
from playwright.async_api import async_playwright
import os

app = FastAPI(title="NotebookLM API", description="将文件上传到 NotebookLM 并生成音频概述")

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_PATH = "/Users/mhlee/tmp/chrome-profile-9922"
PORT = 9922

def start_chrome():
    """启动 Chrome 浏览器"""
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

async def new_notebook(driver, file_path='/Users/mhlee/Work/ke/notebooklm/data/middle.txt', convert_file_type='Audio Overview'):
    """
    创建新的 notebook，上传文件并生成指定类型的输出
    返回下载的文件路径
    """
    download_path = None

    try:
        await driver.get_by_role("button", name="Create new notebook").nth(0).click()
        await asyncio.sleep(3)

        await driver.locator('input[name="Filedata"]').set_input_files(file_path, timeout=0)
        await asyncio.sleep(2)

        # 等待上传完毕
        audio_button = driver.get_by_role("button", name=convert_file_type).nth(0)
        await audio_button.wait_for(state="visible", timeout=30000)

        # 等待按钮可用
        for _ in range(30):  # 最多等 30 秒
            if not await audio_button.is_disabled():
                await audio_button.click()
                print("按钮已点击")
                break
            else:
                await driver.wait_for_timeout(1000)  # 等 1 秒再检查
        else:
            raise Exception("按钮在超时时间内一直是禁用状态")

        print("等待更多按钮出现...")

        for i in range(30):  # 最多检查 30 次
            if await driver.locator('button[aria-label="More"].artifact-more-button').count() > 0:
                await driver.locator('button[aria-label="More"].artifact-more-button').nth(0).click()
                print("已点击更多按钮")
                break
            else:
                print(f"第 {i + 1} 次检查：按钮未出现，等待 30 秒")
                await asyncio.sleep(30)

        # 监听下载事件
        download_event = asyncio.Event()
        download_filename = None

        async def on_download(download):
            nonlocal download_filename
            download_filename = download.suggested_filename
            save_path = f"/Users/mhlee/Work/ke/notebooklm/downloads/{download_filename}"
            print(f"保存文件 -> {save_path}")
            await download.save_as(save_path)
            download_event.set()

        driver.on("download", on_download)

        await driver.get_by_role("menuitem", name="Download").click()

        # 等待下载完成
        try:
            await asyncio.wait_for(download_event.wait(), timeout=300)  # 最长等 5 分钟
            download_path = f"/Users/mhlee/Work/ke/notebooklm/downloads/{download_filename}"
        except asyncio.TimeoutError:
            raise Exception("下载超时")

        return {
            "status": "success",
            "message": "文件处理完成",
            "download_path": download_path,
            "filename": download_filename
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "download_path": download_path
        }

@app.post("/process")
async def process_file(
    file_path: str = '/Users/mhlee/Work/ke/notebooklm/data/middle.txt',
    convert_type: str = 'Audio Overview'
):
    """
    处理文件并生成 NotebookLM 输出

    - **file_path**: 要上传的文件路径
    - **convert_type**: 转换类型，默认为 'Audio Overview'
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail=f"文件不存在: {file_path}")

        # 启动 Chrome（如果还没启动）
        start_chrome()

        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(f"http://localhost:{PORT}")
            context = browser.contexts[0]
            page = context.pages[0]

            print("接管页面成功：", page.url)

            # 导航到 NotebookLM
            await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")

            # 执行处理
            result = await new_notebook(page, file_path, convert_type)

            # 关闭浏览器连接
            await browser.close()

            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result["message"])

            return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API 根路径"""
    return {"message": "NotebookLM API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)