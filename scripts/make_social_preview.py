"""Generate high-resolution 1280x640 GitHub Social Media Preview Card for NewsAlerts."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def create_social_preview(output_path: Path):
    W, H = 1280, 640
    img = Image.new("RGBA", (W, H), (10, 14, 22, 255))
    draw = ImageDraw.Draw(img)

    # 1. Base Gradient Background (Deep Institutional Navy/Black)
    for y in range(H):
        t = y / (H - 1)
        r = int(9 * (1 - t) + 14 * t)
        g = int(12 * (1 - t) + 20 * t)
        b = int(18 * (1 - t) + 32 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # 2. Subtle Background Grid (Faint institutional graph lines)
    grid_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid_layer)
    for x in range(0, W, 40):
        gdraw.line([(x, 0), (x, H)], fill=(255, 255, 255, 6))
    for y in range(0, H, 40):
        gdraw.line([(0, y), (W, y)], fill=(255, 255, 255, 6))
    img = Image.alpha_composite(img, grid_layer)

    # 3. Ambient Radial Glows (Soft Bloom)
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    def draw_glow(cx, cy, radius, color):
        for r in range(radius, 0, -4):
            alpha = int(color[3] * (1.0 - (r / radius) ** 1.6))
            glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(color[0], color[1], color[2], alpha))

    # Mint ambient glow on brand
    draw_glow(220, 160, 280, (34, 201, 147, 30))
    # Indigo ambient glow on right corner
    draw_glow(1080, 480, 360, (99, 102, 241, 45))
    # Electric cyan ambient glow behind terminal
    draw_glow(920, 180, 280, (34, 211, 238, 30))

    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)

    # 4. Load High-DPI Windows Fonts
    font_bold_42 = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 40)
    font_bold_26 = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 24)
    font_bold_16 = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 15)
    font_bold_14 = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13)
    font_reg_15 = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 14)
    font_reg_13 = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 13)
    font_mono_13 = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 13)
    font_mono_11 = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 11)

    # 5. Left Column: Brand Header
    base_dir = Path(__file__).resolve().parent.parent
    icon_path = base_dir / "assets" / "app_icon_transparent.png"
    if icon_path.exists():
        app_icon = Image.open(icon_path).convert("RGBA").resize((58, 58), Image.Resampling.LANCZOS)
        # Background card for logo with emerald glow
        draw.rounded_rectangle([48, 48, 112, 112], radius=14, fill=(16, 23, 38, 255), outline=(34, 201, 147, 120), width=1)
        img.paste(app_icon, (51, 51), app_icon)

    draw.text((126, 48), "NewsAlerts", font=font_bold_42, fill=(255, 255, 255))
    
    # Version Badge
    ver_text = "v2.4.1"
    v_bbox = draw.textbbox((0, 0), ver_text, font=font_mono_13)
    vw = v_bbox[2] - v_bbox[0] + 16
    vx = 126 + 236
    vy = 60
    draw.rounded_rectangle([vx, vy, vx + vw, vy + 24], radius=6, fill=(34, 201, 147, 30), outline=(34, 201, 147, 100), width=1)
    draw.text((vx + 8, vy + 4), ver_text, font=font_mono_13, fill=(52, 211, 153))

    # Slogan / Value Proposition
    draw.text((48, 134), "Real-Time Momentum Intelligence", font=font_bold_26, fill=(52, 211, 153))

    sub_line1 = "Institutional-grade US small-cap momentum screener, high-of-day"
    sub_line2 = "running tape, and zero-lag catalyst news wire built for active day traders."
    draw.text((48, 172), sub_line1, font=font_reg_15, fill=(148, 163, 184))
    draw.text((48, 194), sub_line2, font=font_reg_15, fill=(148, 163, 184))

    # Core Features (with custom glowing indicator dots)
    bullets = [
        ((34, 201, 147), "Zero-Latency Inbound Alerts", "Audio bells & instant Telegram push alerts"),
        ((34, 211, 238), "Running Momentum Tape", "Warrior-style HOD & squeeze breakout prints"),
        ((251, 191, 36), "Zero-Lag Catalyst Wire", "Eliminates retail 5-15 minute charting delay"),
        ((168, 85, 247), "Institutional Short Locates", "Real-time ETB · HTB · NO BORROW badges"),
    ]

    by = 246
    for dot_color, title_txt, desc_txt in bullets:
        # Glowing status dot
        draw.ellipse([48, by + 4, 58, by + 14], fill=dot_color)
        draw.ellipse([46, by + 2, 60, by + 16], outline=(dot_color[0], dot_color[1], dot_color[2], 60), width=1)
        
        draw.text((70, by), title_txt, font=font_bold_16, fill=(255, 255, 255))
        t_bbox = draw.textbbox((70, by), title_txt, font=font_bold_16)
        tx_end = t_bbox[2]
        draw.text((tx_end + 8, by + 1), f"·  {desc_txt}", font=font_reg_13, fill=(100, 116, 139))
        by += 40

    # Architecture & OS Pills at bottom
    pills = [
        ("Windows x64", (34, 201, 147)),
        ("macOS arm64", (34, 201, 147)),
        ("Linux x64", (34, 201, 147)),
        ("~14MB Standalone", (192, 132, 252)),
        ("Zero Electron", (148, 163, 184)),
        ("Native Speed", (148, 163, 184)),
    ]

    px = 48
    py = 556
    for text, text_col in pills:
        bbox = draw.textbbox((0, 0), text, font=font_bold_14)
        pw = bbox[2] - bbox[0] + 18
        ph = 27
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=6, fill=(16, 22, 35, 255), outline=(text_col[0], text_col[1], text_col[2], 90), width=1)
        draw.text((px + 9, py + 5), text, font=font_bold_14, fill=text_col)
        px += pw + 8

    # Helper for rounded corner masks with anti-aliasing
    def round_corners(image: Image.Image, radius: int) -> Image.Image:
        scale = 3
        w, h = image.size
        mask = Image.new("L", (w * scale, h * scale), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0, 0, w * scale - 1, h * scale - 1], radius=radius * scale, fill=255)
        mask = mask.resize((w, h), Image.Resampling.LANCZOS)
        out = image.copy()
        out.putalpha(mask)
        return out

    # 6. Right Side Visual Showcase: Elevated Terminal Window
    terminal_path = base_dir / "docs" / "img" / "terminal.png"
    if terminal_path.exists():
        term_img = Image.open(terminal_path).convert("RGBA")
        term_w, term_h = 585, 345
        term_resized = term_img.resize((term_w, term_h), Image.Resampling.LANCZOS)
        term_rounded = round_corners(term_resized, 12)

        tx, ty = 645, 52

        # Realistic Soft Drop Shadow
        shadow_box = Image.new("RGBA", (term_w + 60, term_h + 60), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow_box)
        sdraw.rounded_rectangle([25, 25, term_w + 25, term_h + 25], radius=16, fill=(0, 0, 0, 200))
        shadow_box = shadow_box.filter(ImageFilter.GaussianBlur(22))
        img.paste(shadow_box, (tx - 25, ty - 25), shadow_box)

        # Border
        draw.rounded_rectangle([tx - 1, ty - 1, tx + term_w + 1, ty + term_h + 1], radius=13, fill=None, outline=(255, 255, 255, 35), width=1)
        img.paste(term_rounded, (tx, ty), term_rounded)

    # 7. Overlaid Floating Strategy Card (Shifted to prevent text overlap)
    strat_path = base_dir / "docs" / "img" / "strategies.png"
    if strat_path.exists():
        strat_img = Image.open(strat_path).convert("RGBA")
        strat_w, strat_h = 250, 245
        strat_resized = strat_img.resize((strat_w, strat_h), Image.Resampling.LANCZOS)
        strat_rounded = round_corners(strat_resized, 10)

        sx, sy = 670, 325

        # Shadow
        strat_shadow = Image.new("RGBA", (strat_w + 50, strat_h + 50), (0, 0, 0, 0))
        ssdraw = ImageDraw.Draw(strat_shadow)
        ssdraw.rounded_rectangle([20, 20, strat_w + 20, strat_h + 20], radius=14, fill=(0, 0, 0, 230))
        strat_shadow = strat_shadow.filter(ImageFilter.GaussianBlur(18))
        img.paste(strat_shadow, (sx - 20, sy - 20), strat_shadow)

        # Border
        draw.rounded_rectangle([sx - 1, sy - 1, sx + strat_w + 1, sy + strat_h + 1], radius=11, fill=None, outline=(34, 201, 147, 90), width=1)
        img.paste(strat_rounded, (sx, sy), strat_rounded)

    # 8. Overlaid Live Inbound Alert Badge
    bx, by = 935, 340
    bw, bh = 295, 66
    # Shadow
    b_shadow = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
    bsdraw = ImageDraw.Draw(b_shadow)
    bsdraw.rounded_rectangle([15, 15, bw + 15, bh + 15], radius=12, fill=(0, 0, 0, 210))
    b_shadow = b_shadow.filter(ImageFilter.GaussianBlur(12))
    img.paste(b_shadow, (bx - 15, by - 15), b_shadow)

    # Banner Card
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(15, 23, 40, 248), outline=(34, 201, 147, 110), width=1)
    # Accent indicator bar on left
    draw.rounded_rectangle([bx, by + 4, bx + 4, by + bh - 4], radius=2, fill=(34, 201, 147, 255))

    # Alert notification tag
    draw.rounded_rectangle([bx + 14, by + 12, bx + 36, by + 32], radius=4, fill=(34, 201, 147, 40))
    draw.text((bx + 20, by + 14), "!", font=font_bold_16, fill=(34, 201, 147))

    draw.text((bx + 46, by + 13), "WORX", font=font_bold_16, fill=(255, 255, 255))
    draw.text((bx + 98, by + 13), "+94.20%", font=font_bold_16, fill=(74, 222, 128))
    
    # HTB tag
    draw.rounded_rectangle([bx + 172, by + 14, bx + 210, by + 30], radius=4, fill=(234, 179, 8, 255))
    draw.text((bx + 177, by + 15), "HTB", font=font_mono_11, fill=(0, 0, 0))

    draw.text((bx + 46, by + 38), "HOD Squeeze · 5m Vol +64,906%", font=font_mono_11, fill=(56, 189, 248))

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"Successfully generated {output_path} ({W}x{H})")


if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent.parent / "assets" / "social_preview.png"
    create_social_preview(out_file)

