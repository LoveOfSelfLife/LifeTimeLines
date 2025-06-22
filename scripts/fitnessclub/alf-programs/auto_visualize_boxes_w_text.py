#!/usr/bin/env python3
import json
import argparse
import os
import xml.sax.saxutils as saxutils

SVG_HEADER = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg
    xmlns=\"http://www.w3.org/2000/svg\"
    width=\"{width}\"
    height=\"{height}\"
    viewBox=\"0 0 {width} {height}\">
  <title>OCR Bounding Boxes with Text</title>
  <desc>Visualizes blocks from structured OCR output with text labels.</desc>
"""

SVG_FOOTER = "</svg>\n"


def load_boxes(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_canvas_size(blocks, margin=10):
    max_x = max(vertex['x'] for b in blocks for vertex in b['bounding_box'])
    max_y = max(vertex['y'] for b in blocks for vertex in b['bounding_box'])
    return max_x + margin, max_y + margin


def block_to_svg_elements(block, stroke_color="#e63946", stroke_width=2, font_size=12, text_color="#000000"):
    verts = block['bounding_box']
    # assuming verts order: top-left, top-right, bottom-right, bottom-left
    x0, y0 = verts[0]['x'], verts[0]['y']
    x1, _  = verts[1]['x'], verts[1]['y']
    _, y3  = verts[3]['x'], verts[3]['y']
    width  = x1 - x0
    height = y3 - y0
    # Rectangle
    rect = (
        f'  <rect x="{x0}" y="{y0}" width="{width}" height="{height}" '
        f'stroke="{stroke_color}" stroke-width="{stroke_width}" fill="none"/>'

    )
    # Text
    text_elems = []
    lines = block['block_text'].split('\n')
    for i, line in enumerate(lines):
        # Each line offset by font_size + 2 pixels
        text_x = x0 + 2
        text_y = y0 + (i + 1) * (font_size + 2)
        safe_text = saxutils.escape(line)
        text_elems.append(
            f'  <text x="{text_x}" y="{text_y}" font-size="{font_size}" fill="{text_color}">'
            f'{safe_text}</text>\n'
        )
    return rect + ''.join(text_elems)


def main():
    import os
    for filename in os.listdir("D:/ALF/structured_outputs/"):
        if filename.endswith(".json"):
            json_path = os.path.join("D:/ALF/structured_outputs/", filename)

            blocks = load_boxes(json_path)
            canvas_w, canvas_h = compute_canvas_size(blocks)

            # Build SVG
            svg_lines = [SVG_HEADER.format(width=canvas_w, height=canvas_h)]
            for block in blocks:
                svg_lines.append(block_to_svg_elements(block))
            svg_lines.append(SVG_FOOTER)

            # Write SVG
            svg_path = os.path.join("D:/ALF/visuals/", filename.replace('.json', '.svg'))
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.writelines(svg_lines)

if __name__ == "__main__":
    main()
