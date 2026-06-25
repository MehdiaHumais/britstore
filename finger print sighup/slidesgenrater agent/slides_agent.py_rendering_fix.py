# ==========================================
# DESIGN UTILITIES (FOOTER & ACCENTS)
# ==========================================
def add_professional_footer(slide, theme, slide_num, total_slides, topic):
    """Adds a consistent professional footer with slide numbers and metadata."""
    is_light = (theme["bg"] == RGBColor(255, 255, 255))
    footer_color = theme["text_dark"] if is_light else theme["text_light"]
    
    # Bottom Horizontal Progress Bar (Subtle)
    bar_width = (13.33 / total_slides) * slide_num
    add_shape(slide, theme["accent"], 0, Inches(7.45), Inches(bar_width), Inches(0.05))
    
    # Page Number (Right)
    add_textbox(slide, 12.0, 7.15, 1.0, 0.3, f"PAGE {slide_num} / {total_slides}", 9, footer_color, False, PP_ALIGN.RIGHT, "Arial")
    
    # Metadata (Left)
    meta_text = f"CONFIDENTIAL | {topic[:40].upper()} | STRATEGIC INVESTOR DECK"
    add_textbox(slide, 0.3, 7.15, 8.0, 0.3, meta_text, 9, footer_color, False, PP_ALIGN.LEFT, "Arial")


def render_hero_slide(slide, theme, item, hero_img=None, slide_num=1, total_slides=10):
    set_background(slide, theme["bg"])
    is_left = (hero_img is not None)
    
    if hero_img:
        try:
            slide.shapes.add_picture(hero_img, 0, 0, height=Inches(7.5))
        except: pass
        # Semi-transparent overlay for text readability
        add_shape(slide, theme["primary"], Inches(7.5), Inches(0), Inches(5.833), Inches(7.5), transparency=0.15)
        tx_left, tx_width = 8.0, 5.0
        align = PP_ALIGN.LEFT
    else:
        add_shape(slide, theme["primary"], 0, 0, Inches(13.33), Inches(7.5))
        tx_left, tx_width = 1.0, 11.33
        align = PP_ALIGN.CENTER

    # Title
    title_txt = item["title"].upper()
    add_textbox(slide, tx_left, 1.8, tx_width, 1.5, title_txt, 44 if len(title_txt) < 30 else 32, theme["text_light"], True, align, "Arial")
    
    # Content
    bullets = item.get("bullets", [])
    txBox = slide.shapes.add_textbox(Inches(tx_left + 0.3), Inches(3.4), Inches(tx_width - 0.6), Inches(3.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    
    for i, b in enumerate(bullets[:5]):
        p = tf.add_paragraph()
        p.font.size = Pt(22 if len(bullets) < 4 else 18)
        p.font.name = "Segoe UI"
        p.alignment = align
        p.space_after = Pt(20)
        
        r1 = p.add_run(); r1.text = "• "; r1.font.color.rgb = theme["accent"]
        r2 = p.add_run(); r2.text = str(b); r2.font.color.rgb = theme["text_light"]

    add_professional_footer(slide, theme, slide_num, total_slides, item["title"])


def render_standard_slide(slide, theme, item, img=None, is_even=True, slide_num=1, total_slides=10):
    set_background(slide, theme["bg"])
    is_light = (theme["bg"] == RGBColor(255, 255, 255))
    text_color = theme["text_dark"] if is_light else theme["text_light"]
    
    # Premium Header
    add_shape(slide, theme["primary"], 0, 0, Inches(13.33), Inches(1.0))
    add_shape(slide, theme["accent"], 0, Inches(1.0), Inches(13.33), Inches(0.04))
    
    # Design Accent (Top Right)
    add_shape(slide, theme["accent"], Inches(12.8), 0, Inches(0.53), Inches(0.53), transparency=0.2)
    
    add_textbox(slide, 0.5, 0.20, 12, 0.7, item["title"].upper(), 32, theme["text_light"], True, PP_ALIGN.LEFT, "Arial")

    # Content Area
    has_img = img is not None
    content_width = 8.2 if has_img else 12.0
    content_left = 0.6 if (not has_img or not is_even) else 4.5
    img_left = 9.2 if not is_even else 0.6

    if has_img:
        try:
            add_shape(slide, theme["accent"], Inches(img_left - 0.1), Inches(1.5), Inches(3.6), Inches(5.3))
            slide.shapes.add_picture(img, Inches(img_left), Inches(1.6), width=Inches(3.4), height=Inches(5.1))
        except: pass

    bullets = item.get("bullets", [])
    txBox = slide.shapes.add_textbox(Inches(content_left + 0.3), Inches(1.2), Inches(content_width - 0.6), Inches(5.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    
    font_size = 24 if len(bullets) <= 4 else 18
    for bullet in bullets[:6]:
        p = tf.add_paragraph()
        p.font.size = Pt(font_size); p.font.color.rgb = text_color
        p.font.name = "Segoe UI"; p.space_after = Pt(15)
        
        if ":" in str(bullet):
            parts = str(bullet).split(":", 1)
            r1 = p.add_run(); r1.text = "• " + parts[0].strip() + ": "; r1.font.bold = True; r1.font.color.rgb = theme["accent"]
            r2 = p.add_run(); r2.text = parts[1].strip(); r2.font.color.rgb = text_color
        else:
            r1 = p.add_run(); r1.text = "• "; r1.font.color.rgb = theme["accent"]
            r2 = p.add_run(); r2.text = str(bullet); r2.font.color.rgb = text_color

    add_professional_footer(slide, theme, slide_num, total_slides, item["title"])


def render_2column_slide(slide, theme, item, slide_num=1, total_slides=10):
    set_background(slide, theme["bg"])
    is_light = (theme["bg"] == RGBColor(255, 255, 255))
    text_color = theme["text_dark"] if is_light else theme["text_light"]

    # Header
    add_shape(slide, theme["primary"], 0, 0, Inches(13.33), Inches(0.9))
    add_shape(slide, theme["accent"], 0, Inches(0.9), Inches(13.33), Inches(0.04))
    add_textbox(slide, 0.5, 0.15, 12, 0.6, item["title"].upper(), 30, theme["text_light"], True, PP_ALIGN.LEFT, "Arial")

    bullets = item.get("bullets", [])
    mid = (len(bullets) + 1) // 2
    col1, col2 = bullets[:mid], bullets[mid:]

    for idx, (col_text, left) in enumerate([(col1, 0.6), (col2, 6.8)]):
        txBox = slide.shapes.add_textbox(Inches(left), Inches(1.3), Inches(5.8), Inches(5.5))
        tf = txBox.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
        
        for bullet in col_text[:6]:
            p = tf.add_paragraph()
            p.font.size = Pt(18); p.font.color.rgb = text_color; p.font.name = "Segoe UI"; p.space_after = Pt(10)
            r1 = p.add_run(); r1.text = "• "; r1.font.color.rgb = theme["accent"]
            r2 = p.add_run(); r2.text = str(bullet); r2.font.color.rgb = text_color

    add_professional_footer(slide, theme, slide_num, total_slides, item["title"])


def render_table_slide(slide, theme, item, slide_num=1, total_slides=10):
    set_background(slide, theme["bg"])
    is_light = (theme["bg"] == RGBColor(255, 255, 255))
    text_color = theme["text_dark"] if is_light else theme["text_light"]

    add_shape(slide, theme["primary"], 0, 0, Inches(13.33), Inches(1.0))
    add_shape(slide, theme["accent"], 0, Inches(1.0), Inches(13.33), Inches(0.04))
    add_textbox(slide, 0.5, 0.20, 12, 0.7, item["title"].upper(), 32, theme["text_light"], True, PP_ALIGN.LEFT, "Arial")

    bullets = item.get("bullets", [])
    # Render financial table or list
    table_top = 1.8; row_height = 0.8
    for i, b in enumerate(bullets[:6]):
        bg = theme["primary"] if i % 2 == 0 else theme["glass"]
        add_shape(slide, bg, Inches(1), Inches(table_top + i*row_height), Inches(11.33), Inches(row_height))
        add_shape(slide, theme["accent"], Inches(1), Inches(table_top + i*row_height), Inches(0.1), Inches(row_height))
        add_textbox(slide, 1.2, table_top + i*row_height, 10.8, row_height, str(b), 20, text_color, False, PP_ALIGN.LEFT)

    add_professional_footer(slide, theme, slide_num, total_slides, item["title"])


def render_section_slide(slide, theme, item, slide_num=1, total_slides=10):
    set_background(slide, theme["primary"])
    add_shape(slide, theme["accent"], Inches(1), Inches(3.5), Inches(11.33), Inches(0.05))
    add_textbox(slide, 1, 2.2, 11.33, 1.2, item["title"].upper(), 48, theme["text_light"], True, PP_ALIGN.CENTER, "Arial")
    if "bullets" in item and item["bullets"]:
        add_textbox(slide, 1, 3.8, 11.33, 1.0, item["bullets"][0], 24, theme["accent"], False, PP_ALIGN.CENTER)
    add_professional_footer(slide, theme, slide_num, total_slides, "SECTION BREAK")


def create_presentation(slides_data, topic, theme, detail_level, include_images=False, output_file="presentation.pptx", pdf_images=None, task_updater=None):
    if not slides_data: return False
    
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]
    
    print(f"[*] Rendering {len(slides_data)} premium slides...")
    total_slides = len(slides_data)

    for i, item in enumerate(slides_data):
        slide = prs.slides.add_slide(blank_slide_layout)
        s_num = i + 1
        if task_updater: task_updater(f"Rendering Slide {s_num}: {item['title'][:15]}...")

        # Image fetching
        img_source = None
        if include_images:
            try:
                if pdf_images and i < len(pdf_images):
                    img_source = pdf_images[i]
                else:
                    query = item.get("visual_query", f"{topic} professional business")
                    with DDGS() as ddgs:
                        res = list(ddgs.images(query, max_results=1))
                        if res:
                            img_url = res[0].get('image') or res[0].get('thumbnail')
                            img_resp = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                            if img_resp.status_code == 200:
                                img_source = io.BytesIO(img_resp.content)
            except Exception as e:
                print(f"[!] Image failed: {e}")

        # Dispatch
        stype = item.get("type", "standard").lower()
        if stype == "hero":
            render_hero_slide(slide, theme, item, img_source, s_num, total_slides)
        elif stype == "2column":
            render_2column_slide(slide, theme, item, s_num, total_slides)
        elif stype == "table":
            render_table_slide(slide, theme, item, s_num, total_slides)
        elif stype == "section":
            render_section_slide(slide, theme, item, s_num, total_slides)
        else:
            render_standard_slide(slide, theme, item, img_source, i % 2 == 0, s_num, total_slides)

    try:
        prs.save(output_file)
        add_fade_transition(output_file)
        return True
    except Exception as e:
        print(f"[!] Save failed: {e}"); return False
