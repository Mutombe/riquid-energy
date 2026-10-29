"""Converts the source photos into web-ready WebP files with semantic names.

Run: python _src/tools/build_images.py <source-folder>
Each photo is written twice: <name>-lg.webp (1800px wide) and <name>-md.webp (900px wide).
"""
import os, sys
from PIL import Image, ImageOps

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/PC/Downloads/riquid"
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "img")

PHOTOS = {
    "harare-skyline": "a690ab84-4d48-41d8-84ca-a9675dda0f43.jpg",
    "harare-city": "istockphoto-1302659815-612x612.jpg",
    "panels-forest": "istockphoto-2222813649-2048x2048.jpg",
    "panels-clouds": "istockphoto-2231745593-2048x2048.jpg",
    "panels-sunset": "istockphoto-2246916593-2048x2048.jpg",
    "panels-crops": "istockphoto-1402475274-2048x2048.jpg",
    "panels-inverters-field": "istockphoto-1130758764-2048x2048.jpg",
    "panels-tracker": "istockphoto-2162813543-2048x2048.jpg",
    "panels-field-green": "solar-power-field-1024x701.jpg",
    "panels-farm-fence": "electric-farm-with-panels-producing-clean-ecologic-energy-1024x683.jpg",
    "agrivoltaic-canopy": "istockphoto-1676495583-2048x2048.jpg",
    "agrivoltaic-rows": "istockphoto-1718847029-2048x2048.jpg",
    "home-solar-roof": "istockphoto-1362872948-2048x2048.jpg",
    "home-roof-dusk": "istockphoto-2254411341-2048x2048.jpg",
    "home-hillside": "vTgfLwZ.jpeg",
    "project-mt-pleasant": "Untitled-711-x-450-px-4.png",
    "project-fitment-centre": "1-1.png",
    "project-warehouse-roof": "2-1.png",
    "installer-sunset": "istockphoto-2209090636-2048x2048.jpg",
    "installer-drill": "image-up.png",
    "engineer-panels": "istockphoto-2286461738-2048x2048.jpg",
    "engineer-vineyard": "istockphoto-1448607390-2048x2048.jpg",
    "engineers-field": "istockphoto-1463617670-2048x2048.jpg",
    "inverters-room": "istockphoto-1197590704-2048x2048.jpg",
    "inverter-battery-wall": "istockphoto-1742670724-2048x2048.jpg",
    "inverter-panel": "istockphoto-1490061322-2048x2048.jpg",
    "inverter-house-wall": "istockphoto-2211089749-2048x2048.jpg",
    "inverters-string": "istockphoto-909265570-2048x2048.jpg",
    "batteries-glow": "istockphoto-1620576275-2048x2048.jpg",
    "battery-cabinet": "istockphoto-2271995989-2048x2048.jpg",
    "battery-rack": "istockphoto-2294102962-2048x2048.jpg",
    "battery-storage-farm": "istockphoto-2172501561-2048x2048.jpg",
    "irrigation-garden": "istockphoto-2160078175-2048x2048.jpg",
    "seedling-hands": "istockphoto-1462151309-2048x2048.jpg",
    "seedling-palm": "istockphoto-2045558460-2048x2048.jpg",
    "leader-world-map": "istockphoto-2269681156-2048x2048.jpg",
    "consultant-office": "istockphoto-2214926216-2048x2048.jpg",
    "community-team": "istockphoto-2220243310-2048x2048.jpg",
    "community-group": "istockphoto-2230159460-2048x2048.jpg",
    "green-architecture": "istockphoto-2199726093-2048x2048.jpg",
    "green-canopy": "istockphoto-2233448310-2048x2048.jpg",
    "sun-sky": "istockphoto-2260659216-2048x2048.jpg",
    "commuters-bikes": "istockphoto-1999953241-2048x2048.jpg",
    "suburb-aerial": "SNAP_NEW_LANDING_PAGE_BANNER_MAR2018.jpg",
    "new-build-homes": "6a5ab63d619cea6270943999_Property Developer Finance jpg.jpg",
}

def save(im, name, width, q):
    im = im.copy()
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, f"{name}.webp"), "WEBP", quality=q, method=6)

for name, fn in PHOTOS.items():
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, fn))).convert("RGB")
    save(im, f"{name}-lg", 1800, 78)
    save(im, f"{name}-md", 900, 76)
    print(name, im.size)

# Logo: split the transparent lockup into mark + wordmark, and make a light variant for dark backgrounds.
logo = Image.open(os.path.join(SRC, "3eaa35aa-53da-42fa-b618-a1929116dd2e_removalai_preview.png")).convert("RGBA")
logo = logo.crop(logo.getbbox())
logo.save(os.path.join(OUT, "logo-full.png"))
px = logo.load()
rows = [any(px[x, y][3] > 40 for x in range(logo.width)) for y in range(logo.height)]
# first fully transparent row band after the mark separates it from the word "RIQUID"
gap = next(y for y in range(int(logo.height * .4), logo.height) if not rows[y])
mark = logo.crop((0, 0, logo.width, gap)); mark = mark.crop(mark.getbbox())
word = logo.crop((0, gap, logo.width, logo.height)); word = word.crop(word.getbbox())
mark.save(os.path.join(OUT, "logo-mark.png"))
word.save(os.path.join(OUT, "logo-word.png"))

def lighten_greys(im):
    im = im.copy(); p = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = p[x, y]
            if a and max(r, g, b) - min(r, g, b) < 40:  # neutral grey -> white
                p[x, y] = (255, 255, 255, a)
    return im
lighten_greys(word).save(os.path.join(OUT, "logo-word-light.png"))
lighten_greys(mark).save(os.path.join(OUT, "logo-mark-light.png"))
print("logo", logo.size, "mark", mark.size, "word", word.size)
