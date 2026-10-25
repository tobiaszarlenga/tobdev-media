import subprocess, time, urllib.parse
from playwright.sync_api import sync_playwright
OUT="/home/claude/work/shots/out/flow"
import os; os.makedirs(OUT,exist_ok=True)
srv=subprocess.Popen(["python3","-m","http.server","8765","--bind","127.0.0.1"],cwd="/home/claude/work/shots/sites",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={"width":390,"height":844},device_scale_factor=2.5,is_mobile=True,has_touch=True)
    pg=ctx.new_page()
    pg.route("**/*",lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") or r.request.url.startswith("data:") else r.abort())
    popups=[]
    ctx.on("page",lambda np: popups.append(np.url))
    pg.add_init_script("window.open=function(u){window.__wa=u;return null}")
    pg.goto("http://127.0.0.1:8765/el-gordo-burger/index.html",wait_until="load"); pg.wait_for_timeout(800)
    h=pg.evaluate("document.documentElement.scrollHeight"); y=0
    while y<h: pg.mouse.wheel(0,500); y+=500; pg.wait_for_timeout(100)
    pg.evaluate("document.querySelector('#menu').scrollIntoView()"); pg.wait_for_timeout(900)
    pg.evaluate("window.scrollBy(0,-10)"); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{OUT}/01-menu.png")
    adds=pg.locator("[data-add]")
    print("adds",adds.count())
    adds.nth(0).scroll_into_view_if_needed(); pg.wait_for_timeout(400)
    pg.screenshot(path=f"{OUT}/02-antes.png")
    adds.nth(0).click(); pg.wait_for_timeout(700)
    pg.screenshot(path=f"{OUT}/03-agregado.png")
    adds=pg.locator("[data-add]")
    adds.nth(1).scroll_into_view_if_needed(); pg.wait_for_timeout(300)
    adds.nth(1).click(); pg.wait_for_timeout(700)
    pg.screenshot(path=f"{OUT}/04-agregado2.png")
    pg.locator("[data-cart-open]").first.click() if pg.locator("[data-cart-open]").count() else pg.locator("#fab-cart, [aria-label*='arrito']").first.click()
    pg.wait_for_timeout(900)
    pg.screenshot(path=f"{OUT}/05-carrito.png")
    pg.fill("#cli-nombre","Tob"); pg.fill("#cli-direccion","Av. Mate de Luna 1800")
    pg.locator("[data-pago='Transferencia']").click(); pg.wait_for_timeout(400)
    pg.locator("#cli-direccion").scroll_into_view_if_needed(); pg.wait_for_timeout(400)
    pg.screenshot(path=f"{OUT}/06-datos.png")
    pg.locator("#cart-checkout").click(); pg.wait_for_timeout(600)
    pg.screenshot(path=f"{OUT}/07-enviar.png")
    u=pg.evaluate("window.__wa||''")
    msg=urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get("text",[""])[0]
    open(f"{OUT}/mensaje.txt","w").write(msg); print(msg)
    b.close()
finally:
  srv.terminate()
