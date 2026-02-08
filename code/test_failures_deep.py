import asyncio
import json
import os
from playwright.async_api import async_playwright

# Danh sách một vài link đại diện từ các nguồn lỗi để test
TEST_LINKS = {
    "bitrss": "https://bitrss.com/vietnam-proposes-0-1-tax-on-crypto-transactions-under-new-regulatory-framework-181292",
    "google_news": "https://news.google.com/rss/articles/CBMitgFBVV95cUxNY29XdjZwOUxKZ21aUkpUSGgwa2lnQkhNMy11bHBnWlBtXy1KU04zSkttVXN2Q1NwME1kLUNXWUQ1d0g2ejAtR2x2OG5NTGhlYmxVQ2Z3TkZhYUY3SzFkbFZVOGlKeWRPNzh6VmtyeEZUX1ZETEtVbUFxaDRieEFRankwMm5ORjIyUkpsUHdHQmVJdTRTdEotNG81NWFWWUtJZGtNNlY2UjgyM1MzaGJzYjhIeDJVZw?oc=5",
    "cryptonews": "https://cryptonews.com/news/investors-pour-258m-into-crypto-startups-despite-2t-market-wipeout/",
    "livebitcoinnews": "https://www.livebitcoinnews.com/russias-sberbank-prepares-corporate-crypto-backed-lending/"
}

async def scrape_test(name, url, context):
    print(f"\n--- Testing source: {name} ---")
    print(f"URL: {url}")
    try:
        page = await context.new_page()
        # Giả lập User-Agent xịn hơn
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        })
        
        # Thử đợi kết quả tải xong hoàn toàn
        response = await page.goto(url, wait_until="networkidle", timeout=30000)
        
        status = response.status if response else "No Response"
        title = await page.title()
        content = await page.evaluate("() => document.body.innerText")
        
        print(f"Status: {status}")
        print(f"Title: {title[:50]}...")
        print(f"Content Length: {len(content)} characters")
        
        if len(content) < 500:
            print("⚠️ CẢNH BÁO: Nội dung quá ngắn, có thể bị chặn hoặc trang trắng.")
        else:
            print("✅ Thành công: Đã lấy được nội dung.")
            
        await page.close()
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        for name, url in TEST_LINKS.items():
            await scrape_test(name, url, context)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
