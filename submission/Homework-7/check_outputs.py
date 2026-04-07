import json

with open('ARIA_v4.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

lines_out = [f"Total cells: {len(nb['cells'])}\n"]
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        outputs = cell.get('outputs', [])
        all_text = []
        for out in outputs:
            if out.get('output_type') == 'error':
                lines_out.append(f"=== ERROR Cell {i}: {out.get('ename')}: {out.get('evalue')} ===\n")
            txt = out.get('text', '')
            if txt:
                lines = txt if isinstance(txt, list) else [txt]
                all_text.extend(lines)
        j = ''.join(all_text).strip()
        if j:
            lines_out.append(f"--- Cell {i} ---\n")
            lines_out.append(j[:600] + "\n\n")

with open('outputs_summary.txt', 'w', encoding='utf-8') as f:
    f.writelines(lines_out)

print("Done. Written to outputs_summary.txt")
