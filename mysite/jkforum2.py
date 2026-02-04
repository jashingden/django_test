from playwright.sync_api import Playwright, sync_playwright, expect
import time

home = "https://jkforum.net"

def get_tid(link):
    idx = link.index("thread-")
    start = idx+7
    end = link.index("-", start)
    tid = link[start:end]
    return tid

def get_title(title):
    idx = title.find(']')
    if idx > 0:
        title = title[idx+1:]
        title = title if title.find('\n') == -1 else title[0:title.find('\n')]
    return title if len(title) <= 50 else title[0:50]

def get_title2(title):
    idx = title.find('<span class="">')
    if idx > 0:
        title = title[idx+15:title.find('</span>', idx+15)]
        title = title if title.find('\n') == -1 else title[0:title.find('\n')]
    return title if len(title) <= 50 else title[0:50]

def parse_url(playwright: Playwright, url: str, times: int = 1) -> None:
    start_url = home + url

    # 啟動瀏覽器，headless=False 會顯示瀏覽器畫面，方便除錯
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    # 前往目標網頁
    page.goto(start_url)

    # 處理 "我已滿18歲" 的確認彈窗
    try:
        # 等待 "不再提醒" 的 checkbox 出現，最多等5秒
        page.get_by_role("checkbox", name="不再提醒").wait_for(timeout=5000)
        page.get_by_role("checkbox", name="不再提醒").check()
        page.get_by_test_id("pass-button").click()
    except Exception:
        pass

    # 模擬向下捲動頁面以載入更多文章
    print(f"捲動次數: {times}")
    for _ in range(7, times*7):
        page.mouse.wheel(0, 1000) # 捲動距離可以依據網頁調整
        time.sleep(3) # 等待新內容載入

    # 找到所有文章的連結元素
    post_links = page.locator('a[href*="thread-"]').all()
    print(f"文章數量: {len(post_links)}")

    # 遍歷每一篇文章連結
    for i, link_locator in enumerate(post_links):
        #if i >= 1:
        #    break

        print(f"\ninner_text: {link_locator.inner_text()}\n\ninner_html: {link_locator.inner_html()}")
        name = get_title(link_locator.inner_text())
        if len(name) == 0:
            name = get_title2(link_locator.inner_html())
        href = link_locator.get_attribute("href")
        tid = get_tid(href)
        content_url = home + href

        print(f"\n--- 正在處理第 {i+1} 篇文章 ---")
        print(f"標題: {name}")
        print(f"tid: {tid}")
        print(f"URL: {content_url}")

        if i >= 1:
            continue

        # 因為連結是 target="_blank"，會在新分頁中開啟
        # 我們需要捕捉這個新分頁
        with context.expect_page() as new_page_info:
            link_locator.click()
        
        post_page = new_page_info.value
        time.sleep(3) # 等待新內容載入

        try:
            # 取得第一個帖子的內文
            # 使用 first 來確保只抓取到第一個符合條件的元素
            content_element = post_page.locator(".mb-7-5").first
            content = content_element.inner_text()
            html = content_element.inner_html()
            ll = content_element.get_by_role("link").all()
            content = content + f"\n\n\n連結數量: {len(ll)}\n"
            for _, l in enumerate(ll):
                content = content + f"連結: {l.get_attribute('href')}\n"

            print(f"內文: {content}")
            print(f"HTML: {html}")
        except Exception:
            pass
        finally:
            # 關閉文章分頁，回到列表頁
            post_page.close()

    # ---------------------    
    context.close()
    browser.close()


with sync_playwright() as playwright:
    url = "/p/type-1128-1476.html"
    parse_url(playwright, url, times=1)
