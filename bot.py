def make_image(title, text, footer, icon_text="❓"):
    width, height = 1200, 675

    # تحميل الخلفية
    if os.path.exists("background.png"):
        img = Image.open("background.png").convert("RGB")
        img = img.resize((width, height))
    else:
        img = Image.new("RGB", (width, height), "#101010")

    draw = ImageDraw.Draw(img)

    # البحث عن خط يدعم العربية
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
    ]

    font_path = None

    for path in font_candidates:
        if os.path.isfile(path):
            font_path = path
            break

    if font_path is None:
        raise RuntimeError(
            "لم يتم العثور على خط عربي في السيرفر."
        )

    # تحميل الخطوط
    title_font = ImageFont.truetype(font_path, 48)
    text_font = ImageFont.truetype(font_path, 52)
    footer_font = ImageFont.truetype(font_path, 28)
    icon_font = ImageFont.truetype(font_path, 45)

    # تنسيق النص العربي
    def centered(txt, y, font, fill):
        shaped = arabic(txt)
        box = draw.textbbox((0, 0), shaped, font=font)
        x = (width - (box[2] - box[0])) // 2
        draw.text((x, y), shaped, font=font, fill=fill)

    # العنوان
    centered(title, 80, title_font, "#e32636")

    # صندوق السؤال
    box_box = (150, 200, 1050, 470)

    draw.rounded_rectangle(
        box_box,
        radius=25,
        fill="#0f0505",
        outline="#e32636",
        width=4
    )

    # تقسيم السؤال إلى أسطر
    words = str(text).split()
    lines = []
    line = ""

    for word in words:
        test = (line + " " + word).strip()
        shaped = arabic(test)

        if draw.textlength(shaped, font=text_font) > 800 and line:
            lines.append(line)
            line = word
        else:
            line = test

    if line:
        lines.append(line)

    # وضع السؤال بوسط الصندوق
    total_height = len(lines) * 70
    y = 200 + (270 - total_height) // 2

    for current_line in lines:
        centered(current_line, y, text_font, "white")
        y += 70

    # الرموز الجانبية
    try:
        draw.text((180, 310), icon_text, font=icon_font, fill="white")
        draw.text((980, 310), icon_text, font=icon_font, fill="white")
    except Exception:
        pass

    # التذييل
    centered(footer, 595, footer_font, "#dddddd")

    # حفظ الصورة
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer