import os
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

FONT_SIZE = 24
HZK_FILE = "HZK24H"
OUTPUT_TTF = "hzk24.ttf"

if not os.path.exists(HZK_FILE):
    print(f"错误: 找不到 {HZK_FILE} 文件！")
    exit()

# 自动检测精简版和完整版字库
file_size = os.path.getsize(HZK_FILE)
start_qian = 1 if file_size >= 580000 else 16
offset_base = start_qian

with open(HZK_FILE, "rb") as f:
    hzk_data = f.read()

# 提取字符
chars = []
for qian in range(start_qian, 88):
    if 10 <= qian <= 15: continue
    for wei in range(1, 95):
        try:
            char_bytes = bytes([qian + 160, wei + 160])
            char_str = char_bytes.decode("gb2312")
            offset = ((qian - offset_base) * 94 + (wei - 1)) * 72
            chars.append((char_str, offset))
        except UnicodeDecodeError:
            continue

print("【1/3】正在构建字体轮廓...")

# 设置字体度量（每个像素放大100倍，让字体清晰）
unitsPerEm = 2400
scale = unitsPerEm // FONT_SIZE # 100

glyphs = {}
cmap = {}
glyphOrder = [".notdef"]

# 基础缺省字形（黑方块，防止字体报错）
pen = TTGlyphPen(None)
pen.moveTo((0, 0))
pen.lineTo((0, unitsPerEm))
pen.lineTo((unitsPerEm, unitsPerEm))
pen.lineTo((unitsPerEm, 0))
pen.closePath()
glyphs[".notdef"] = pen.glyph()

# 逐个绘制像素
for idx, (char_str, offset) in enumerate(chars):
    if offset + 72 > len(hzk_data): break
    
    glyph_bytes = hzk_data[offset:offset+72]
    pen = TTGlyphPen(None)
    
    has_pixels = False
    for y in range(FONT_SIZE):
        for x_byte in range(3):
            byte_val = glyph_bytes[y * 3 + x_byte]
            for bit in range(8):
                if (byte_val >> (7 - bit)) & 1:
                    has_pixels = True
                    x = x_byte * 8 + bit
                    # 绘制像素方块，注意 TTF 的坐标原点在左下角
                    x0 = x * scale
                    y0 = (FONT_SIZE - 1 - y) * scale 
                    x1 = (x + 1) * scale
                    y1 = (FONT_SIZE - y) * scale
                    
                    pen.moveTo((x0, y0))
                    pen.lineTo((x1, y0))
                    pen.lineTo((x1, y1))
                    pen.lineTo((x0, y1))
                    pen.closePath()
    
    if has_pixels:
        glyph_name = f"uni{ord(char_str):04X}"
        glyphs[glyph_name] = pen.glyph()
        cmap[ord(char_str)] = glyph_name
        glyphOrder.append(glyph_name)

print(f"【2/3】共生成 {len(glyphOrder)-1} 个字形，正在写入 TTF 结构...")

# 构建 TTF
fb = FontBuilder(unitsPerEm, isTTF=True)
fb.setupGlyphOrder(glyphOrder)
fb.setupCharacterMap(cmap)
fb.setupGlyf(glyphs)

# 设置间距
metrics = {".notdef": (unitsPerEm, 0)}
for name in glyphOrder[1:]:
    metrics[name] = (unitsPerEm, 0)
fb.setupHorizontalMetrics(metrics)

fb.setupHorizontalHeader(ascent=unitsPerEm, descent=0)
fb.setupNameTable({"familyName": "hzk24", "styleName": "Regular"})
fb.setupOS2(sTypoAscender=unitsPerEm, sTypoDescender=0, usWinAscent=unitsPerEm, usWinDescent=0)
fb.setupPost()

fb.save(OUTPUT_TTF)
print(f"【3/3】成功！已直接生成完美兼容 Windows 的 hzk24.ttf 文件！")