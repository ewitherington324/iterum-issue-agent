"""One-off extraction of Iterum's real fault taxonomy from Issue Category Analysis.xlsx.

Reads the "Fault Categories" sheet and writes taxonomy.json. Stdlib only (xlsx is a zip
of XML), so this runs before any dependencies are installed.

Run from the project root:  python data/extract_taxonomy.py
"""

import json
import re
import sys
import zipfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "Issue Category Analysis.xlsx"
OUT = Path(__file__).resolve().parent / "taxonomy.json"


def _shared_strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    xml = z.read("xl/sharedStrings.xml").decode("utf-8")
    out = []
    for si in re.findall(r"<si>(.*?)</si>", xml, re.S):
        # a string item may be split across several <t> runs
        out.append("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
    return [_unescape(s) for s in out]


def _unescape(s):
    return (
        s.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&amp;", "&")
    )


def _rows(z, sheet, strings):
    xml = z.read(sheet).decode("utf-8")
    rows = []
    for row_xml in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
        cells = {}
        for cell in re.findall(r"<c\s([^>]*?)/?>(?:(.*?)</c>)?", row_xml, re.S):
            attrs, body = cell
            ref = re.search(r'r="([A-Z]+)\d+"', attrs)
            if not ref:
                continue
            col = ref.group(1)
            ctype = re.search(r't="(\w+)"', attrs)
            ctype = ctype.group(1) if ctype else "n"
            if ctype == "inlineStr":
                value = "".join(re.findall(r"<t[^>]*>(.*?)</t>", body or "", re.S))
                value = _unescape(value)
            else:
                v = re.search(r"<v>(.*?)</v>", body or "", re.S)
                value = _unescape(v.group(1)) if v else ""
                if ctype == "s" and value != "":
                    value = strings[int(value)]
            cells[col] = value.strip()
        rows.append(cells)
    return rows


def slugify(appliance, category):
    base = f"{appliance} {category}".lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    return base.strip("_")


def main():
    if not SOURCE.exists():
        sys.exit(f"Source workbook not found: {SOURCE}")

    with zipfile.ZipFile(SOURCE) as z:
        strings = _shared_strings(z)
        rows = _rows(z, "xl/worksheets/sheet1.xml", strings)

    # Locate the header row, then read until the data stops.
    header_idx = None
    for i, r in enumerate(rows):
        values = [v.lower() for v in r.values()]
        if any("appliance" in v for v in values) and any("issue category" in v for v in values):
            header_idx = i
            header = r
            break
    if header_idx is None:
        sys.exit("Could not find the header row on the Fault Categories sheet.")

    col = {}
    for ref, name in header.items():
        key = name.lower()
        if key.startswith("appliance"):
            col["appliance"] = ref
        elif "issue category" in key:
            col["category"] = ref
        elif "label slug" in key or key == "slug":
            col["slug"] = ref
        elif "frequency (count)" in key:
            col["count"] = ref

    taxonomy = {}
    current_appliance = None
    for r in rows[header_idx + 1:]:
        appliance = r.get(col.get("appliance", ""), "").strip()
        category = r.get(col.get("category", ""), "").strip()
        if appliance:
            current_appliance = appliance
        if not category or not current_appliance:
            continue
        # stop at the free-text notes below the table
        if category.endswith("?") or len(category) > 60:
            continue

        slug = r.get(col.get("slug", ""), "").strip() or slugify(current_appliance, category)
        count = r.get(col.get("count", ""), "").strip()
        entry = {"category": category, "slug": slug}
        if count:
            try:
                entry["observed_count"] = int(float(count))
            except ValueError:
                pass
        taxonomy.setdefault(current_appliance, []).append(entry)

    OUT.write_text(json.dumps(taxonomy, indent=2) + "\n")
    total = sum(len(v) for v in taxonomy.values())
    print(f"Wrote {OUT.name}: {len(taxonomy)} appliance types, {total} fault categories")
    for appliance, cats in taxonomy.items():
        print(f"  {appliance}: {len(cats)}")


if __name__ == "__main__":
    main()
