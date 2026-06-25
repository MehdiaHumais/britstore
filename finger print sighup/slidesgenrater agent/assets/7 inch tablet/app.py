from PIL import Image

# Open the image
img = Image.open("6.png").convert("RGBA")

# Use 'getbbox' to find the actual content (ignores the transparent edges)
bbox = img.getbbox()

if bbox:
    # Crop the image to just the UI
    cropped_img = img.crop(bbox)
    
    # Now resize the cropped UI to hit that 1080px requirement
    # For a tablet, we'll set the width to 1920 (Landscape 16:9)
    target_width = 1920
    w_percent = (target_width / float(cropped_img.size[0]))
    target_height = int((float(cropped_img.size[1]) * float(w_percent)))
    
    final_img = cropped_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Save it
    final_img.convert("RGB").save("cropped_tablet_screenshot.png")
    print("Cropped and resized to fit!")