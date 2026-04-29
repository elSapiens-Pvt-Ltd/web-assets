#!/usr/bin/env python3
"""
BNI Presentation Asset Setup Script
Downloads improved Unsplash images, copies Dawn's photo,
and updates the HTML to use local assets.
"""

import os
import shutil
import urllib.request
import ssl

BASE_DIR = "/Users/dawndharmishtan/Desktop/bni/30april2026"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HTML_FILE = os.path.join(BASE_DIR, "index.html")
DAWN_SOURCE = os.path.join(BASE_DIR, "WhatsApp Image 2026-02-25 at 17.30.56.jpeg")
DAWN_DEST = os.path.join(ASSETS_DIR, "dawn.jpg")

MIN_SIZE_BYTES = 50 * 1024  # 50 KB

# ── Images to download ──────────────────────────────────────────────
IMAGES = [
    {
        "filename": "bg-title.jpg",
        "primary_id": "photo-1620712943543-bcc4688e7485",
        "fallback_id": "photo-1677442135703-1787eea5ce01",
        "purpose": "Title — dramatic AI/futuristic glow",
    },
    {
        "filename": "bg-scattered.jpg",
        "primary_id": "photo-1586769852044-692d6e3703f0",
        "fallback_id": "photo-1568992687947-868a62a9f521",
        "purpose": "Problem — overwhelmed/chaos",
    },
    {
        "filename": "bg-team.jpg",
        "primary_id": "photo-1600880292203-757bb62b4baf",
        "fallback_id": "photo-1522071820081-009f0129c71c",
        "purpose": "Transformation — positive team",
    },
    {
        "filename": "bg-future.jpg",
        "primary_id": "photo-1451187580459-43490279c0fa",
        "fallback_id": "photo-1518770660439-4636190af475",
        "purpose": "Future — grand scale/aspirational",
    },
]

# Current Unsplash URLs in the HTML → local asset filename mapping
# (ordered to match the replacements we need to make)
HTML_URL_MAP = [
    # (current_url_in_html, local_asset_filename)
    (
        "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=1920&q=85&fit=crop&auto=format",
        "bg-title.jpg",
    ),
    (
        "https://images.unsplash.com/photo-1568992687947-868a62a9f521?w=1920&q=85&fit=crop&auto=format",
        "bg-scattered.jpg",
    ),
    (
        "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1920&q=85&fit=crop&auto=format",
        "bg-team.jpg",
    ),
    (
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1920&q=85&fit=crop&auto=format",
        "bg-future.jpg",
    ),
    (
        "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=1200&q=85&fit=crop&auto=format",
        "dawn.jpg",
    ),
]


def build_url(photo_id: str) -> str:
    return (
        f"https://images.unsplash.com/{photo_id}"
        f"?w=1920&q=88&fit=crop&auto=format"
    )


def download_image(url: str, dest_path: str, label: str) -> bool:
    """Attempt to download url → dest_path. Returns True if file > MIN_SIZE_BYTES."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()
        if len(data) < MIN_SIZE_BYTES:
            print(f"  [SKIP] {label}: downloaded {len(data)//1024} KB — too small (<50 KB)")
            return False
        with open(dest_path, "wb") as f:
            f.write(data)
        print(f"  [OK]   {label}: {len(data)//1024} KB  →  {os.path.basename(dest_path)}")
        return True
    except Exception as exc:
        print(f"  [FAIL] {label}: {exc}")
        return False


# ── Step 1: Create assets dir and copy Dawn's photo ─────────────────
print("=" * 60)
print("STEP 1 — Create assets dir & copy Dawn's photo")
print("=" * 60)

os.makedirs(ASSETS_DIR, exist_ok=True)
print(f"  Directory: {ASSETS_DIR}")

if os.path.exists(DAWN_SOURCE):
    shutil.copy2(DAWN_SOURCE, DAWN_DEST)
    dawn_size = os.path.getsize(DAWN_DEST)
    print(f"  [OK]   dawn.jpg copied — {dawn_size // 1024} KB")
    dawn_ok = True
else:
    print(f"  [FAIL] Source not found: {DAWN_SOURCE}")
    dawn_ok = False

# ── Step 2: Download Unsplash images ────────────────────────────────
print()
print("=" * 60)
print("STEP 2 — Download Unsplash images")
print("=" * 60)

download_results = {}  # filename → bool (success)

for img in IMAGES:
    fname = img["filename"]
    dest = os.path.join(ASSETS_DIR, fname)
    primary_url = build_url(img["primary_id"])
    fallback_url = build_url(img["fallback_id"])

    print(f"\n  [{fname}]  {img['purpose']}")
    print(f"  Trying primary  ({img['primary_id']})…")
    ok = download_image(primary_url, dest, "primary")

    if not ok:
        print(f"  Trying fallback ({img['fallback_id']})…")
        ok = download_image(fallback_url, dest, "fallback")

    download_results[fname] = ok
    if not ok:
        print(f"  [WARN] Both primary and fallback failed for {fname}.")

# ── Step 3: Update the HTML ──────────────────────────────────────────
print()
print("=" * 60)
print("STEP 3 — Update HTML")
print("=" * 60)

with open(HTML_FILE, "r", encoding="utf-8") as f:
    html = f.read()

original_html = html
replacements_done = []
replacements_skipped = []

for current_url, asset_filename in HTML_URL_MAP:
    asset_path = os.path.join(ASSETS_DIR, asset_filename)
    local_ref = f"assets/{asset_filename}"

    # Determine success: dawn.jpg uses dawn_ok, others use download_results
    if asset_filename == "dawn.jpg":
        asset_ok = dawn_ok and os.path.exists(asset_path) and os.path.getsize(asset_path) > MIN_SIZE_BYTES
    else:
        asset_ok = download_results.get(asset_filename, False)

    if asset_ok and current_url in html:
        html = html.replace(current_url, local_ref)
        replacements_done.append(f"  [REPLACED]  {current_url}\n             → {local_ref}")
    elif not asset_ok:
        replacements_skipped.append(f"  [SKIPPED]   {current_url}  (asset not available)")
    elif current_url not in html:
        replacements_skipped.append(f"  [NOT FOUND] {current_url}  (URL not present in HTML)")

if html != original_html:
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTML written: {HTML_FILE}")
else:
    print("  No changes needed (HTML already up-to-date or all assets failed).")

for r in replacements_done:
    print(r)
for r in replacements_skipped:
    print(r)

# ── Final asset summary ──────────────────────────────────────────────
print()
print("=" * 60)
print("FINAL ASSET SUMMARY")
print("=" * 60)

all_assets = [img["filename"] for img in IMAGES] + ["dawn.jpg"]
for fname in all_assets:
    fpath = os.path.join(ASSETS_DIR, fname)
    if os.path.exists(fpath):
        size_kb = os.path.getsize(fpath) / 1024
        status = "OK" if size_kb * 1024 > MIN_SIZE_BYTES else "SMALL"
        print(f"  [{status:5}]  {fpath}  ({size_kb:.1f} KB)")
    else:
        print(f"  [MISSING]  {fpath}")

print()
print("Done.")
