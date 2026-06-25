from PIL import Image

# 1. Open the original image
img = Image.open("banner.png")

# 2. Resize using Resampling.LANCZOS for the best quality scaling
# (LANCZOS helps prevent the lines from looking blurry or pixelated)
resized_img = img.resize((1024, 500), Image.Resampling.LANCZOS)

# 3. Save the new file
resized_img.save("banner_size.png")

print("Image resized successfully!")