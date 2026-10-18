from PIL import Image, ImageFilter
import numpy as np

SRC = r"static\images\store.png"
OUT_LOGO = r"static\images\logo.png"
OUT_TOUCH = r"static\images\apple-touch-icon.png"

im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(np.int16)
h, w, _ = a.shape

bg = np.array([232, 238, 246])
dist = np.sqrt(((a - bg) ** 2).sum(2))

mask = np.zeros((h, w), bool)
mask[0, :] = mask[-1, :] = mask[:, 0] = mask[:, -1] = True
mask &= dist <= 45

for _ in range(6000):
    g = mask.copy()
    g[1:, :] |= mask[:-1, :]
    g[:-1, :] |= mask[1:, :]
    g[:, 1:] |= mask[:, :-1]
    g[:, :-1] |= mask[:, 1:]
    nm = g & (dist <= 45)
    if np.array_equal(nm, mask):
        break
    mask = nm

strict = int(mask.sum())

# feather the anti-aliased edge (looser tolerance, but only expanding outward)
for _ in range(3):
    g = mask.copy()
    g[1:, :] |= mask[:-1, :]
    g[:-1, :] |= mask[1:, :]
    g[:, 1:] |= mask[:, :-1]
    g[:, :-1] |= mask[:, 1:]
    mask = g & (dist <= 100)

alpha = np.where(mask, 0, 255).astype(np.uint8)
rgba = np.dstack([np.asarray(im), alpha])

content = np.where(alpha > 0)
bbox = (int(content[1].min()), int(content[0].min()), int(content[1].max()), int(content[0].max()))

# smooth the cut-out edge by ~1px so it does not look jagged
out = Image.fromarray(rgba, "RGBA").resize((512, 512), Image.LANCZOS)
r, g_, b_, al = out.split()
al = al.filter(ImageFilter.GaussianBlur(0.7))
out = Image.merge("RGBA", (r, g_, b_, al))
out.save(OUT_LOGO, optimize=True)

# apple-touch-icon must stay opaque (iOS composites transparency onto black)
flat = Image.new("RGB", out.size, (255, 255, 255))
flat.paste(out, (0, 0), out)
flat.resize((180, 180), Image.LANCZOS).save(OUT_TOUCH, optimize=True)

np.save("logs/_bgtmp_mask.npy", mask)
print("size", im.size)
print("removed(strict border fill)", strict, f"{strict/(h*w)*100:.1f}%")
print("removed(total after feather)", int(mask.sum()), f"{mask.sum()/(h*w)*100:.1f}%")
print("kept content bbox", bbox)
print("kept pixels", int((alpha > 0).sum()))
print("wrote", OUT_LOGO, OUT_TOUCH)
