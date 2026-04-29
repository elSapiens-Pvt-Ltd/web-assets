#!/usr/bin/env python3
"""Download 4 final brand-matched background images for the BNI presentation."""
import os, ssl, urllib.request

ASSETS = "/Users/dawndharmishtan/Desktop/bni/30april2026/assets"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

IMAGES = [
    # Circuit board — tech / AI feel (already dark teal tones)
    ("bg-tech.jpg",  "photo-1518770660439-4636190af475"),
    # Earth at night from space — scattered city lights / grand scale
    ("bg-earth.jpg", "photo-1451187580459-43490279c0fa"),
    # LA city skyline at night — deep blue confirmed from preview session
    ("bg-city.jpg",  "photo-1444723121867-7a241cacace9"),
    # Dark analytics dashboard — data / metrics / impact
    ("bg-data.jpg",  "photo-1551288049-bebda4e38f71"),
]

for fname, photo_id in IMAGES:
    dest = os.path.join(ASSETS, fname)
    url  = f"https://images.unsplash.com/{photo_id}?w=1920&q=88&fit=crop&auto=format"
    req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    print(f"Downloading {fname}…", end=" ", flush=True)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"{len(data)//1024} KB  ✓")
    except Exception as e:
        print(f"FAILED: {e}")

print("Done.")
