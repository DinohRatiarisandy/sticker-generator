from nicegui import ui
from PIL import Image, ImageFilter
from rembg import remove

from io import BytesIO
import base64
import os

os.makedirs("temp", exist_ok=True)

# ---------- GLOBAL STATE ----------

cutout_image = None


# Pastel colors
PASTEL_COLORS = {
    "Blue": (173, 216, 230, 255),
    "Pink": (255, 209, 220, 255),
    "Green": (198, 255, 221, 255),
    "Yellow": (255, 255, 204, 255),
    "Purple": (230, 210, 255, 255),
}

# ---------- HELPERS ----------


def pil_to_base64(img: Image.Image):

    buffer = BytesIO()

    img.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{encoded}"


def clean_alpha(img: Image.Image, threshold=140):

    img = img.convert("RGBA")

    data = img.get_flattened_data()

    new_data = []

    for r, g, b, a in data:
        if a < threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, 255))

    img.putdata(new_data)

    return img


def generate_preview(border_size, bg_color):

    global cutout_image

    if cutout_image is None:
        return

    # Pillow MaxFilter requires odd number >= 3
    border_size = max(3, border_size)

    if border_size % 2 == 0:
        border_size += 1

    # Alpha mask
    alpha = cutout_image.getchannel("A")

    # Outline mask
    outline_mask = alpha.filter(ImageFilter.MaxFilter(border_size))

    # White outline
    outline = Image.new("RGBA", cutout_image.size, (255, 255, 255, 0))

    outline.putalpha(outline_mask)

    # Merge
    sticker = Image.alpha_composite(outline, cutout_image)

    # Crop transparent empty space
    bbox = sticker.getbbox()

    sticker = sticker.crop(bbox)

    # Background canvas
    padding = 40

    final = Image.new(
        "RGBA", (sticker.width + padding * 2, sticker.height + padding * 2), bg_color
    )

    final.paste(sticker, (padding, padding), sticker)

    preview.source = pil_to_base64(final)

    # Save export
    final.save("temp/output.png")


def download():
    ui.download("temp/output.png")


# Upload
async def on_upload(e):

    global cutout_image

    uploaded_file = e.file

    file_bytes = await uploaded_file.read()

    image = Image.open(BytesIO(file_bytes)).convert("RGBA")

    # Remove background once
    cutout_image = remove(image)

    cutout_image = clean_alpha(cutout_image)

    generate_preview(border_slider.value, PASTEL_COLORS[color_select.value])


# ---------- UI ----------

ui.label("Sticker Generator").classes("text-2xl")

preview = ui.image().classes("w-96")


ui.upload(on_upload=on_upload, auto_upload=True).props("accept=image/*")


# Border slider
border_slider = ui.slider(min=3, max=51, value=15)

border_slider.on(
    "update:model-value",
    lambda: generate_preview(border_slider.value, PASTEL_COLORS[color_select.value]),
)


# Color select
color_select = ui.select(options=list(PASTEL_COLORS.keys()), value="Blue")

color_select.on(
    "update:model-value",
    lambda: generate_preview(border_slider.value, PASTEL_COLORS[color_select.value]),
)


# Download button
ui.button("Download PNG", on_click=download)

ui.run()
