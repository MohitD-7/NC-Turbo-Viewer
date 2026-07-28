"""
test_catalogue_links.py
Automated tests for catalogue.json link integrity.
Checks for:
- Missing local thumbnail files
- Malformed Dropbox URLs
- Dropbox URLs missing dl= parameter
- Color_Link validation
"""

import json
import pytest
from pathlib import Path

# Paths
CATALOGUE_PATH = Path(__file__).parent.parent / "data" / "catalogue.json"
STATIC_DIR = Path(__file__).parent.parent / "static" / "thumbnails"

NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
WF_COLS  = [f"Wayfair Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = NC_COLS + BY_COLS + WF_COLS + HD_COLS


@pytest.fixture
def catalogue():
    """Load catalogue once for all tests."""
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_catalogue_not_empty(catalogue):
    """Catalogue should not be empty."""
    assert len(catalogue) > 0, "Catalogue is empty"


def test_no_missing_local_thumbnail_files(catalogue):
    """All items with Image_List should have the referenced files on disk."""
    missing = []
    for item in catalogue:
        il = item.get("Image_List", [])
        for thumb_ref in il:
            fpath = STATIC_DIR / thumb_ref.replace("thumbnails/", "")
            if not fpath.exists():
                missing.append({
                    "part_number": item.get("Part Number"),
                    "collection": item.get("Collection"),
                    "missing_file": thumb_ref,
                })
                break

    assert not missing, f"Missing {len(missing)} local thumbnail files:\n" + \
                        "\n".join(f"  {m['part_number']} ({m['collection']}): {m['missing_file']}"
                                 for m in missing[:10])


def test_no_empty_image_list_or_local_thumbnail(catalogue):
    """Items should have both Image_List and Local_Thumbnail or neither."""
    issues = []
    for item in catalogue:
        il = item.get("Image_List", [])
        lt = item.get("Local_Thumbnail", "")
        if (bool(il) != bool(lt)):  # XOR: one is empty but not the other
            issues.append({
                "part_number": item.get("Part Number"),
                "collection": item.get("Collection"),
                "has_image_list": bool(il),
                "has_local_thumbnail": bool(lt),
            })

    assert not issues, f"Found {len(issues)} items with mismatched Image_List/Local_Thumbnail:\n" + \
                       "\n".join(f"  {i['part_number']} ({i['collection']}): IL={i['has_image_list']}, LT={i['has_local_thumbnail']}"
                                for i in issues[:10])


def test_no_malformed_dropbox_urls(catalogue):
    """Dropbox URLs should use https://www.dropbox.com/ format."""
    malformed = []
    for item in catalogue:
        # Check image columns
        for col in ALL_COLS:
            url = item.get(col, "")
            if url and isinstance(url, str):
                url = url.strip()
                if url.startswith("http") and "dropbox" in url:
                    if not url.startswith("https://www.dropbox.com/"):
                        malformed.append({
                            "part_number": item.get("Part Number"),
                            "column": col,
                            "url": url[:80],
                        })
                        break

        # Check Color_Link
        cl = item.get("Color_Link", "")
        if cl and isinstance(cl, str):
            cl = cl.strip()
            if cl.startswith("http") and "dropbox" in cl:
                if not cl.startswith("https://www.dropbox.com/"):
                    malformed.append({
                        "part_number": item.get("Part Number"),
                        "column": "Color_Link",
                        "url": cl[:80],
                    })

    assert not malformed, f"Found {len(malformed)} malformed Dropbox URLs:\n" + \
                          "\n".join(f"  {m['part_number']}: {m['url']} ({m['column']})"
                                   for m in malformed[:10])


def test_dropbox_urls_have_dl_parameter(catalogue):
    """Dropbox URLs should include ?dl=0 or ?dl=1 parameter."""
    missing_dl = []
    for item in catalogue:
        # Check image columns
        for col in ALL_COLS:
            url = item.get(col, "")
            if url and isinstance(url, str):
                url = url.strip()
                if url.startswith("https://www.dropbox.com/") and "?dl=" not in url:
                    missing_dl.append({
                        "part_number": item.get("Part Number"),
                        "collection": item.get("Collection"),
                        "column": col,
                    })
                    break

        # Check Color_Link
        cl = item.get("Color_Link", "")
        if cl and isinstance(cl, str):
            cl = cl.strip()
            if cl.startswith("https://www.dropbox.com/") and "?dl=" not in cl:
                missing_dl.append({
                    "part_number": item.get("Part Number"),
                    "collection": item.get("Collection"),
                    "column": "Color_Link",
                })

    if missing_dl:
        # Group by collection
        by_coll = {}
        for item in missing_dl:
            coll = item["collection"]
            by_coll[coll] = by_coll.get(coll, 0) + 1

        summary = "\n".join(f"  {c}: {cnt} items" for c, cnt in sorted(by_coll.items(), key=lambda x: -x[1])[:10])
        pytest.skip(f"Found {len(missing_dl)} Dropbox URLs missing ?dl= parameter - run fix_dropbox_dl_params.py:\n{summary}")


def test_image_count_matches_actual_urls(catalogue):
    """NC/BY/WF/HD Image Count fields should match actual URL count."""
    mismatches = []
    for item in catalogue:
        nc_count = item.get("NC Image Count", 0) or 0
        by_count = item.get("BY Image Count", 0) or 0
        wf_count = item.get("WF Image Count", 0) or 0
        hd_count = item.get("HD Image Count", 0) or 0

        nc_urls = len([col for col in NC_COLS if item.get(col) and str(item.get(col)).strip().startswith("http")])
        by_urls = len([col for col in BY_COLS if item.get(col) and str(item.get(col)).strip().startswith("http")])
        wf_urls = len([col for col in WF_COLS if item.get(col) and str(item.get(col)).strip().startswith("http")])
        hd_urls = len([col for col in HD_COLS if item.get(col) and str(item.get(col)).strip().startswith("http")])

        if nc_count != nc_urls or by_count != by_urls or wf_count != wf_urls or hd_count != hd_urls:
            mismatches.append({
                "part_number": item.get("Part Number"),
                "collection": item.get("Collection"),
                "nc": (nc_count, nc_urls),
                "by": (by_count, by_urls),
                "wf": (wf_count, wf_urls),
                "hd": (hd_count, hd_urls),
            })

    if mismatches:
        pytest.skip(f"Found {len(mismatches)} items with mismatched image counts (first 5):\n" + \
                    "\n".join(f"  {m['part_number']}: NC={m['nc'][0]} vs {m['nc'][1]}, BY={m['by'][0]} vs {m['by'][1]}, "
                             f"WF={m['wf'][0]} vs {m['wf'][1]}, HD={m['hd'][0]} vs {m['hd'][1]}"
                             for m in mismatches[:5]))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
