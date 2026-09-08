"""Generate subtle deterministic tileable PBR textures; no external imagery used.

Run using a Python interpreter with NumPy and Pillow. All fields are periodic.
Base colors are sRGB; roughness and OpenGL tangent-space normals are linear data.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "textures"
OUT.mkdir(parents=True, exist_ok=True)
TAU = 2 * np.pi


def noise(n, seed, frequency=5, stretch=(1, 1)):
    """Periodic band-limited noise with independent seeded phases."""
    rng = np.random.default_rng(seed)
    spectrum = np.fft.rfft2(rng.normal(size=(n, n)))
    fx = np.fft.rfftfreq(n) * n / stretch[0]
    fy = np.fft.fftfreq(n) * n / stretch[1]
    radius = np.hypot(fx[None, :], fy[:, None])
    spectrum *= np.exp(-0.5 * (radius / frequency) ** 2)
    spectrum[0, 0] = 0
    a = np.fft.irfft2(spectrum, s=(n, n))
    return a / (a.std() + 1e-9)


def unit(a):
    return np.clip(0.5 + 0.16 * a, 0, 1)


def color(hexstr):
    return np.array([int(hexstr[i:i+2], 16) for i in (0, 2, 4)]) / 255


def blend(a, b, t):
    return color(a)[None, None, :] * (1-t[..., None]) + color(b)[None, None, :] * t[..., None]


stats = {}


def save(name, base, rough, height, tile_m=1.0):
    n = height.shape[0]
    # Image rows point down, whereas the OpenGL tangent-space v axis points up.
    dx = (np.roll(height, -1, 1)-np.roll(height, 1, 1)) / (2*tile_m/n)
    dy = (np.roll(height, -1, 0)-np.roll(height, 1, 0)) / (2*tile_m/n)
    normal = np.stack((-dx, dy, np.ones_like(height)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    for suffix, values in (("basecolor", base), ("roughness", rough), ("normal", normal * .5 + .5)):
        data = np.rint(np.clip(values, 0, 1) * 255).astype(np.uint8)
        Image.fromarray(data).save(OUT / f"pbr_{name}_{suffix}.png", optimize=True)
    stats[name] = {
        "size": n,
        "tile_m": tile_m,
        "roughness_min_max": [float(rough.min()), float(rough.max())],
        "normal_max_deviation_degrees": float(np.rad2deg(np.arccos(normal[..., 2])).max()),
        "basecolor_mean_srgb": [float(v) for v in base.mean(axis=(0, 1))],
    }


def stone():
    n = 1024
    broad, medium, fine = (noise(n, 11, 4), noise(n, 12, 23), noise(n, 13, 145))
    t = np.clip(.43 + broad*.14 + medium*.065 + fine*.018, 0, 1)
    # Sparse mineral seams in a periodic distorted geologic field.
    y, x = np.mgrid[:n, :n] / n
    warp = noise(n, 14, 2.5)
    field = np.sin(TAU*(2*x+y) + warp*.65) + .35*noise(n, 15, 5)
    vein = np.exp(-(field/.033)**2) * np.clip((noise(n, 16, 3)-.3)*.7, 0, 1)
    base = blend("444953", "7c8185", t)
    base = base*(1-vein[..., None]*.35) + color("b4b7b5")*vein[..., None]*.35
    rough = np.clip(.278 + broad*.012 + medium*.008 + fine*.003 - vein*.024, .22, .34)
    height = medium*.000018 + fine*.000005 + vein*.000015
    save("stone", base, rough, height, 1.5)


def charcoal():
    n = 512
    broad, grit = noise(n, 21, 9), noise(n, 22, 150)
    value = broad*.008 + grit*.004
    base = np.clip(color("17191b")+value[..., None], 0, 1)
    rough = np.clip(.625 + broad*.017 + grit*.011, .55, .70)
    save("charcoal", base, rough, broad*.000035 + grit*.000024)


def brass():
    n = 512
    broad, fine = noise(n, 31, 5), noise(n, 32, 52)
    t = np.clip(.5 + broad*.13 + fine*.037, 0, 1)
    base = blend("786045", "ae9161", t)
    rough = np.clip(.365 + broad*.014 + fine*.008, .30, .43)
    save("brass", base, rough, broad*.000012 + fine*.000004)


def oak():
    n = 512
    y, x = np.mgrid[:n, :n] / n
    broad = noise(n, 41, 4, (5, .35))
    fine = noise(n, 42, 16, (5, .25))
    warp = noise(n, 43, 2, (1, .6))
    grain = np.sin(TAU*x*34 + warp*2.2 + .5*np.sin(TAU*y))
    pores = np.maximum(0, grain)**10
    base = color("342a23") + broad[..., None]*np.array([.012, .009, .006])
    base += fine[..., None]*np.array([.005, .004, .003])
    base -= pores[..., None]*np.array([.009, .007, .005])
    rough = np.clip(.413 + broad*.014 + fine*.006 + pores*.014, .34, .48)
    save("oak", base, rough, broad*.000015 + fine*.000008 - pores*.000018)


def fabric():
    n = 512
    y, x = np.mgrid[:n, :n] / n
    warp = np.cos(TAU*x*128)
    weft = np.cos(TAU*y*128)
    weave = warp*.5 + weft*.5 + .25*warp*weft
    irregular = noise(n, 51, 105)
    broad = noise(n, 52, 7)
    base = color("1b1c24") + (weave*.003 + irregular*.0014 + broad*.002)[..., None]
    rough = np.clip(.88 + weave*.013 + irregular*.007, .8, .94)
    save("fabric", base, rough, weave*.000028 + irregular*.000002)


def concrete():
    n = 512
    broad, medium, fine = noise(n, 61, 4), noise(n, 62, 22), noise(n, 63, 125)
    value = broad*.012 + medium*.006 + fine*.003
    base = color("827d70") + value[..., None]
    pores = np.maximum(fine-1.55, 0)
    base -= pores[..., None]*.01
    rough = np.clip(.695 + broad*.016 + medium*.01 + fine*.009, .60, .78)
    save("concrete", base, rough, medium*.00007 + fine*.000055 - pores*.000025)


if __name__ == "__main__":
    for make in (stone, charcoal, brass, oak, fabric, concrete):
        make()
    (OUT / "pbr_recipes.json").write_text(json.dumps(stats, indent=2)+"\n")
    (OUT / "pbr_recipes.md").write_text("""# Procedural PBR textures

Generated by `restaurant/scripts/generate_pbr.py` with fixed NumPy seeds, periodic Fourier noise, and restrained periodic grain/weave functions. These materials contain no source photography.

Basecolor PNGs contain intended sRGB values. Set roughness and normal images to Non-Color. Normals are tangent-space OpenGL +Y; connect through a Normal Map node at strength 1.0. All texture coordinates repeat seamlessly.

Recommended square tile sizes: stone 1.5 m (1–2 m suitable); charcoal, brass, oak, fabric, concrete 1 m. Oak grain runs along image vertical/v. Fabric weave is intentionally subdued at this texel density; for a close camera, 0.25–0.5 m tiles may read better, with reduced normal strength. Oak maps describe continuous wood grain; model floorboard seams separately.

Stone is polished blue-gray mottling with sparse pale mineral seams, not a deeply displaced surface. Charcoal has fine plaster grain. Brass uses subtle aged warm mottling; set metallic to 1.0 (other materials metallic 0). Oak is cocoa-brown longitudinal grain. Fabric is navy-charcoal with a quiet woven surface. Concrete is a warm gray, with fine pores.

Maps are 8-bit PNGs. Stone is 1024 square; others are 512 square. `pbr_recipes.json` records generated roughness ranges and normal deviation. These are procedural approximations for this environment, not calibrated scans of the restaurant materials.
""")
    sheet = Image.new("RGB", (768, 552), "#202124")
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(stats):
        thumb = Image.open(OUT/f"pbr_{name}_basecolor.png").resize((256, 256))
        x, y = (i%3)*256, (i//3)*276
        sheet.paste(thumb, (x,y))
        draw.text((x+8, y+258), name, fill="white")
    sheet.save(OUT/"pbr_preview.png")
    print(json.dumps(stats, indent=2))
