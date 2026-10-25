import subprocess, time, json
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(["python3","-m","http.server","8765","--bind","127.0.0.1"],cwd="/home/claude/work/shots/sites",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
CTA={"el-gordo-burger":"VER MENÚ Y PEDIR","casa-pan":"Ver la carta","torneo-jogo":"INSCRIBÍ TU EQUIPO","infinity-labs":"Consultar por WhatsApp","malala-sombreros":"Encargá tu pieza","ferulas-tuc":"Consultar por WhatsApp","d12tinto":"CONSULTÁ POR WHATSAPP"}
out={}
def frac(bb,vw=390,vh=844): return [round((bb["x"]+bb["width"]/2)/vw,3), round((bb["y"]+bb["height"]/2)/vh,3)]
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    for n,txt in CTA.items():
        ctx=b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True)
        pg=ctx.new_page(); pg.route("**/*",lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
        pg.goto(f"http://127.0.0.1:8765/{n}/index.html",wait_until="load"); pg.wait_for_timeout(1500)
        loc=pg.get_by_text(txt,exact=False)
        bb=None
        for i in range(loc.count()):
            x=loc.nth(i).bounding_box()
            if x and x["y"]>0 and x["y"]<844 and x["width"]>0: bb=x; break
        out[n]=frac(bb) if bb else None
        ctx.close()
    # flujo gordo
    ctx=b.new_context(viewport={"width":390,"height":844},device_scale_factor=2.5,is_mobile=True,has_touch=True)
    pg=ctx.new_page(); pg.route("**/*",lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
    pg.add_init_script("window.open=function(u){window.__wa=u;return null}")
    pg.goto("http://127.0.0.1:8765/el-gordo-burger/index.html",wait_until="load"); pg.wait_for_timeout(800)
    h=pg.evaluate("document.documentElement.scrollHeight"); y=0
    while y<h: pg.mouse.wheel(0,500); y+=500; pg.wait_for_timeout(100)
    pg.evaluate("document.querySelector('#menu').scrollIntoView()"); pg.wait_for_timeout(900); pg.evaluate("window.scrollBy(0,-10)"); pg.wait_for_timeout(300)
    adds=pg.locator("[data-add]"); adds.nth(0).scroll_into_view_if_needed(); pg.wait_for_timeout(400)
    out["f02_agregar"]=frac(adds.nth(0).bounding_box()); adds.nth(0).click(); pg.wait_for_timeout(700)
    adds=pg.locator("[data-add]"); adds.nth(1).scroll_into_view_if_needed(); pg.wait_for_timeout(300)
    out["f03b_agregar2"]=frac(adds.nth(1).bounding_box()); pg.screenshot(path="out/flow/03b-antes2.png"); adds.nth(1).click(); pg.wait_for_timeout(700)
    out["f04_carrito"]=frac(pg.locator("[data-cart-open]").first.bounding_box()); pg.locator("[data-cart-open]").first.click(); pg.wait_for_timeout(900)
    pg.fill("#cli-nombre","Tob"); pg.fill("#cli-direccion","Av. Mate de Luna 1800"); pg.locator("#cli-direccion").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
    out["f06_transf"]=frac(pg.locator("[data-pago='Transferencia']").bounding_box()); pg.locator("[data-pago='Transferencia']").click(); pg.wait_for_timeout(400)
    out["f07_enviar"]=frac(pg.locator("#cart-checkout").bounding_box())
    b.close()
finally: srv.terminate()
json.dump(out,open("out/toques.json","w"),indent=1); print(json.dumps(out))
