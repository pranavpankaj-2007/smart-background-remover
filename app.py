import io
import hashlib
import time

import numpy as np
import streamlit as st
from PIL import Image, ImageFilter, ImageChops
from rembg import remove

st.set_page_config(page_title="Smart Background Remover", page_icon="✂️", layout="wide")
st.title("✂️ Smart Background Remover")
st.caption("Remove the background once, then adjust all seven settings with a live preview.")


@st.cache_data(show_spinner=False, max_entries=3)
def cached_remove_background(image_bytes, max_side=1280):
    """Cached AI removal: changing sliders will not rerun the model."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_size = image.size
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    result = remove(buf.getvalue())
    cutout = Image.open(io.BytesIO(result)).convert("RGBA")
    if cutout.size != original_size:
        cutout = cutout.resize(original_size, Image.Resampling.LANCZOS)
    out = io.BytesIO()
    cutout.save(out, format="PNG")
    return out.getvalue()


def fit_background(image, size):
    w, h = size
    scale = max(w / image.width, h / image.height)
    image = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
    left = (image.width - w) // 2
    top = (image.height - h) // 2
    return image.crop((left, top, left + w, top + h))


def refine_alpha(alpha, softness):
    if softness <= 0:
        return alpha
    blurred = alpha.filter(ImageFilter.GaussianBlur(0.2 + softness * 1.0))
    return Image.blend(alpha, blurred, min(softness, 0.65))


def remove_edge_halo(cutout, background_rgb, strength):
    if strength <= 0:
        return cutout
    rgba = np.asarray(cutout.convert("RGBA")).copy()
    rgb = rgba[:, :, :3].astype(np.float32)
    alpha = rgba[:, :, 3].astype(np.uint8)
    aimg = Image.fromarray(alpha, mode="L")
    edge_band = ImageChops.subtract(
        aimg.filter(ImageFilter.MaxFilter(5)),
        aimg.filter(ImageFilter.MinFilter(5)),
    )
    edge = np.asarray(edge_band, dtype=np.float32) / 255.0
    alpha_f = alpha.astype(np.float32) / 255.0
    partial = np.clip((1.0 - alpha_f) * 1.8, 0.0, 1.0)
    amount = np.clip((edge * partial * strength / 100.0 * 0.55)[:, :, None], 0, 0.55)
    target = np.asarray(background_rgb, dtype=np.float32).reshape(1, 1, 3)
    rgba[:, :, :3] = np.clip(rgb * (1.0 - amount) + target * amount, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def tone_subject(cutout, brightness, warmth):
    rgba = np.asarray(cutout.convert("RGBA")).copy()
    rgb = rgba[:, :, :3].astype(np.float32)
    rgb *= brightness
    rgb[:, :, 0] *= 1.0 + warmth * 0.08
    rgb[:, :, 2] *= 1.0 - warmth * 0.08
    rgba[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def make_shadow(alpha, size, strength, softness, vertical_offset):
    mask = alpha.filter(ImageFilter.GaussianBlur(radius=max(0.1, softness)))
    mask = mask.point(lambda p: int(p * strength / 100.0))
    shifted = Image.new("L", size, 0)
    shifted.paste(mask, (0, int(vertical_offset)))
    shadow = Image.new("RGBA", size, (22, 20, 20, 0))
    shadow.putalpha(shifted)
    return shadow


def composite(cutout, background, shadow_strength, shadow_softness, shadow_offset):
    base = background.convert("RGBA")
    if shadow_strength > 0:
        shade = make_shadow(
            cutout.getchannel("A"), cutout.size,
            shadow_strength, shadow_softness, shadow_offset
        )
        base = Image.alpha_composite(base, shade)
    return Image.alpha_composite(base, cutout.convert("RGBA"))


def checkerboard(image):
    w, h = image.size
    tile = 18
    bg = Image.new("RGB", (w, h), (238, 238, 238))
    px = bg.load()
    for y in range(h):
        for x in range(w):
            if ((x // tile) + (y // tile)) % 2:
                px[x, y] = (198, 198, 198)
    out = bg.convert("RGBA")
    out.alpha_composite(image.convert("RGBA"))
    return out.convert("RGB")


# Sidebar: all seven requested controls stay available.
with st.sidebar:
    st.header("Live editing")
    bg_mode = st.radio("Background", ["Solid colour", "Custom image", "Transparent"])

    colour_name = st.selectbox(
        "Solid background colour",
        ["Warm beige", "Soft cream", "Dusty rose", "Muted sage", "Slate blue", "White", "Black", "Custom"],
    )
    colours = {
        "Warm beige": "#E8D5BD", "Soft cream": "#F1E7D5",
        "Dusty rose": "#E7C5C7", "Muted sage": "#C9D4C2",
        "Slate blue": "#B9C9D8", "White": "#FFFFFF", "Black": "#000000",
    }
    if colour_name == "Custom":
        bg_hex = st.color_picker("Choose colour", "#E8D5BD")
    else:
        bg_hex = colours[colour_name]

    custom_bg_file = None
    bg_blur = 0.0
    if bg_mode == "Custom image":
        custom_bg_file = st.file_uploader("Upload background image", type=["png", "jpg", "jpeg", "webp"])
        bg_blur = st.slider("Background blur", 0.0, 20.0, 0.0, 1.0)

    st.divider()
    edge_blending = st.slider("Edge colour blending", 0, 100, 35)
    edge_softness = st.slider("Edge softness", 0.0, 1.0, 0.30, 0.05)
    shadow_strength = st.slider("Shadow strength", 0, 60, 22)
    shadow_softness = st.slider("Shadow softness", 4, 40, 22)
    shadow_offset = st.slider("Shadow vertical offset", 0, 35, 10)
    subject_brightness = st.slider("Subject brightness", 0.90, 1.10, 1.00, 0.01)
    subject_warmth = st.slider("Subject warmth", -1.0, 1.0, 0.0, 0.1)

uploaded = st.file_uploader("Upload a photo", type=["png", "jpg", "jpeg", "webp"])
if uploaded is None:
    st.info("Upload a photo. The AI removes its background once; the settings below then update the preview.")
    st.stop()

input_bytes = uploaded.getvalue()
source_key = hashlib.sha256(input_bytes).hexdigest()

# Keep a preview-size copy for fast pixel operations. Cached AI cutout stays reusable.
try:
    start = time.perf_counter()
    with st.spinner("Removing background for this photo… this step runs once per image."):
        cutout_bytes = cached_remove_background(input_bytes, 1280)
    cutout_original = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")
    source = Image.open(io.BytesIO(input_bytes)).convert("RGB")
    source.load()

    # Fast interactive preview capped at 1000px; full-resolution cutout retained for export.
    preview_cutout = cutout_original.copy()
    preview_cutout.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
    preview_size = preview_cutout.size
    source_preview = source.copy()
    source_preview.thumbnail((1000, 1000), Image.Resampling.LANCZOS)

    # Build selected background at preview resolution.
    if bg_mode == "Transparent":
        background_preview = None
        background_rgb = None
    elif bg_mode == "Solid colour":
        background_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
        background_preview = Image.new("RGBA", preview_size, (*background_rgb, 255))
    else:
        if custom_bg_file is None:
            st.warning("Upload a custom background image in the sidebar.")
            st.stop()
        bg_img = Image.open(custom_bg_file).convert("RGB")
        bg_img = fit_background(bg_img, preview_size)
        if bg_blur:
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(bg_blur))
        background_rgb = bg_img.resize((1, 1)).getpixel((0, 0))
        background_preview = bg_img.convert("RGBA")

    # Live edit happens on the small preview only. It does not call rembg.
    alpha = refine_alpha(preview_cutout.getchannel("A"), edge_softness)
    preview_cutout.putalpha(alpha)
    if background_rgb is not None:
        preview_cutout = remove_edge_halo(preview_cutout, background_rgb, edge_blending)

    if bg_mode == "Transparent":
        preview_result = preview_cutout
    else:
        adjusted = tone_subject(preview_cutout, subject_brightness, subject_warmth)
        preview_result = composite(
            adjusted, background_preview, shadow_strength, shadow_softness, shadow_offset
        )

    st.subheader("Live preview")
    left, right = st.columns(2)
    with left:
        st.markdown("**Before**")
        st.image(source_preview, use_container_width=True)
    with right:
        st.markdown("**After — updates when you move a setting**")
        if bg_mode == "Transparent":
            st.image(checkerboard(preview_result), use_container_width=True)
        else:
            st.image(preview_result.convert("RGB"), use_container_width=True)

    st.caption(
        f"Preview updated in {time.perf_counter() - start:.2f}s. "
        "The AI removal result is cached, so changing the seven sliders does not run the model again."
    )

    # Full-size final image is generated only on explicit download click.
    if st.button("Prepare full-resolution download"):
        with st.spinner("Preparing full-resolution result…"):
            full = cutout_original.copy()
            full.putalpha(refine_alpha(full.getchannel("A"), edge_softness))
            if bg_mode == "Transparent":
                final = full
            else:
                if bg_mode == "Solid colour":
                    full_bg = Image.new("RGBA", full.size, (*background_rgb, 255))
                else:
                    full_bg = fit_background(Image.open(custom_bg_file).convert("RGB"), full.size)
                    if bg_blur:
                        full_bg = full_bg.filter(ImageFilter.GaussianBlur(bg_blur))
                    full_bg = full_bg.convert("RGBA")
                full = remove_edge_halo(full, background_rgb, edge_blending)
                full = tone_subject(full, subject_brightness, subject_warmth)
                final = composite(full, full_bg, shadow_strength, shadow_softness, shadow_offset)

            out = io.BytesIO()
            final.save(out, format="PNG")
            st.download_button(
                "Download PNG",
                data=out.getvalue(),
                file_name="background_removed.png" if bg_mode == "Transparent" else "background_replaced.png",
                mime="image/png",
            )

except Exception as error:
    st.error("Could not process this image.")
    st.exception(error)
