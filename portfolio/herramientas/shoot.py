import sys, time, subprocess, os
from playwright.sync_api import sync_playwright

ROOT = "/home/claude/work/shots"
OUT = f"{ROOT}/out"
os.makedirs(OUT, exist_ok=True)
names = sys.argv[1:]
srv = subprocess.Popen(["python3", "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=f"{ROOT}/sites",
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)


def settle(page):
    h = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < h:
        page.mouse.wheel(0, 500)
        y += 500
        page.wait_for_timeout(120)
        h = page.evaluate("document.documentElement.scrollHeight")
    page.wait_for_timeout(600)
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(900)


try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n in names:
            for kind, vp, dpr in (("desk", {"width": 1440, "height": 900}, 1.5), ("mob", {"width": 390, "height": 844}, 2)):
                ctx = b.new_context(viewport=vp, device_scale_factor=dpr, is_mobile=(kind == "mob"), has_touch=(kind == "mob"))
                page = ctx.new_page()
                page.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") or r.request.url.startswith("data:") else r.abort())
                page.goto(f"http://127.0.0.1:8765/{n}/index.html", wait_until="load", timeout=30000)
                page.wait_for_timeout(800)
                settle(page)
                page.screenshot(path=f"{OUT}/{n}-{kind}.png")
                h = page.evaluate("document.documentElement.scrollHeight")
                page.screenshot(path=f"{OUT}/{n}-{kind}-full.png", full_page=True,
                                clip={"x": 0, "y": 0, "width": vp["width"], "height": min(h, 9000)})
                ctx.close()
            print("OK", n, flush=True)
        b.close()
finally:
    srv.terminate()
