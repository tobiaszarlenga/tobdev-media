"""Prepara una copia local de cada sitio estático (Tailwind Play CDN + Google Fonts bloqueados en la nube):
compila Tailwind v3 con la config inline y reemplaza Google Fonts por Fontsource locales."""
import os, re, shutil, subprocess, sys, glob, urllib.parse

ROOT = "/home/claude/work/shots"
FS = f"{ROOT}/node_modules/@fontsource"
SRC = sys.argv[1]           # carpeta del sitio
NAME = sys.argv[2]
DST = f"{ROOT}/sites/{NAME}"
if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(".git", "node_modules"))
html = open(f"{DST}/index.html", encoding="utf-8").read()

# --- Tailwind config inline ---
cfg_js = ""
m = re.search(r"<script>\s*(tailwind\.config\s*=[\s\S]*?)</script>", html)
if m:
    cfg_js = m.group(1)
tw_styles = re.findall(r'<style type="text/tailwindcss">([\s\S]*?)</style>', html)
plugins = []
pm = re.search(r'cdn\.tailwindcss\.com\?plugins=([^"]+)"', html)
if pm:
    plugins = pm.group(1).split(",")
open(f"{DST}/tailwind.config.js", "w").write(
    "var tailwind = {};\n" + cfg_js + "\n"
    "var c = tailwind.config || {};\n"
    "c.content = ['./index.html', './**/*.js'];\n"
    + "".join(f"c.plugins = (c.plugins||[]).concat(require('{ROOT}/node_modules/@tailwindcss/{p}'));\n" for p in plugins if p in ("forms", "typography"))
    + "module.exports = c;\n")
open(f"{DST}/tw-in.css", "w").write("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n" + "\n".join(tw_styles))
subprocess.run([f"{ROOT}/node_modules/.bin/tailwindcss", "-c", f"{DST}/tailwind.config.js", "-i", f"{DST}/tw-in.css", "-o", f"{DST}/tw.css"],
               cwd=DST, check=True, capture_output=True)
html = re.sub(r'<script src="https://cdn\.tailwindcss\.com[^"]*"></script>',
              '<link rel="stylesheet" href="tw.css"><script>window.tailwind={};</script>', html)
html = re.sub(r'<style type="text/tailwindcss">[\s\S]*?</style>', "", html)

# --- Google Fonts -> Fontsource ---
faces = []
for gm in re.finditer(r'href="(https://fonts\.googleapis\.com/css2\?[^"]+)"', html):
    q = urllib.parse.urlparse(gm.group(1).replace("&amp;", "&")).query
    for fam in urllib.parse.parse_qs(q).get("family", []):
        name = fam.split(":")[0].replace("+", " ")
        fid = name.lower().replace(" ", "-")
        d = f"{FS}/{fid}/files"
        if not os.path.isdir(d):
            print("SIN FUENTE", name)
            continue
        os.makedirs(f"{DST}/_fonts", exist_ok=True)
        for f in glob.glob(f"{d}/{fid}-latin-*.woff2"):
            mm = re.match(rf"{fid}-latin-(\d+)-(normal|italic)\.woff2$", os.path.basename(f))
            if not mm:
                continue
            shutil.copy(f, f"{DST}/_fonts/")
            faces.append(f"@font-face{{font-family:'{name}';font-style:{mm.group(2)};font-weight:{mm.group(1)};font-display:block;"
                         f"src:url(_fonts/{os.path.basename(f)}) format('woff2')}}")
open(f"{DST}/fonts.css", "w").write("\n".join(faces))
html = re.sub(r'<link[^>]*href="https://fonts\.googleapis\.com/css2[^"]*"[^>]*>', '<link rel="stylesheet" href="fonts.css">', html, count=1)
html = re.sub(r'<link[^>]*href="https://fonts\.googleapis\.com/css2[^"]*"[^>]*>', '', html)
open(f"{DST}/index.html", "w", encoding="utf-8").write(html)
print("OK", NAME, len(faces), "faces", os.path.getsize(f"{DST}/tw.css"), "bytes css")
