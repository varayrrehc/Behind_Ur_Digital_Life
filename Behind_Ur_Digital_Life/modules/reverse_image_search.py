import os
import re
import io
import json
import hashlib
import mimetypes
import urllib.parse
from datetime import datetime

from PIL import Image, ExifTags, ImageChops, ImageStat

try:
    import imagehash
except ImportError:
    imagehash = None

try:
    import pytesseract
except ImportError:
    pytesseract = None


# ============================================================
# CONFIGURATION
# ============================================================

MAX_IMAGE_SIZE_MB = 50

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
}


# ============================================================
# BASIC FILE VALIDATION
# ============================================================

def validate_image_file(image_path):
    """
    Validate that the supplied file is a readable image.

    Returns:
        dict
    """

    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "file": image_path,
    }

    if not image_path:
        result["errors"].append("No image path supplied.")
        return result

    if not os.path.exists(image_path):
        result["errors"].append("Image file does not exist.")
        return result

    if not os.path.isfile(image_path):
        result["errors"].append("Provided path is not a file.")
        return result

    try:
        size = os.path.getsize(image_path)
    except OSError as exc:
        result["errors"].append(f"Unable to read file size: {exc}")
        return result

    size_mb = size / (1024 * 1024)

    result["file_size_bytes"] = size
    result["file_size_mb"] = round(size_mb, 3)

    if size_mb > MAX_IMAGE_SIZE_MB:
        result["errors"].append(
            f"Image exceeds {MAX_IMAGE_SIZE_MB} MB limit."
        )
        return result

    extension = os.path.splitext(image_path)[1].lower()

    result["extension"] = extension

    if extension not in SUPPORTED_EXTENSIONS:
        result["warnings"].append(
            f"Extension '{extension}' is not in the preferred image list."
        )

    try:
        with Image.open(image_path) as img:
            img.verify()

        with Image.open(image_path) as img:
            result["format"] = img.format
            result["width"] = img.width
            result["height"] = img.height
            result["mode"] = img.mode

        result["valid"] = True

    except Exception as exc:
        result["errors"].append(
            f"File is not a valid readable image: {exc}"
        )

    return result


# ============================================================
# FILE HASHES
# ============================================================

def calculate_file_hashes(image_path):
    """
    Calculate cryptographic hashes of the complete file.
    """

    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with open(image_path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            md5.update(chunk)
            sha256.update(chunk)

    return {
        "md5": md5.hexdigest(),
        "sha256": sha256.hexdigest(),
    }


# ============================================================
# PERCEPTUAL HASHES
# ============================================================

def calculate_perceptual_hashes(image_path):
    """
    Calculate perceptual hashes.

    These are useful for finding visually similar images,
    unlike SHA-256 which only identifies exact files.
    """

    if imagehash is None:
        return {
            "error": "ImageHash is not installed. Run: pip install ImageHash"
        }

    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")

            return {
                "ahash": str(imagehash.average_hash(img)),
                "dhash": str(imagehash.dhash(img)),
                "phash": str(imagehash.phash(img)),
                "whash": str(imagehash.whash(img)),
            }

    except Exception as exc:
        return {
            "error": str(exc)
        }


# ============================================================
# EXIF / METADATA
# ============================================================

def _convert_exif_value(value):
    """
    Convert EXIF values into JSON-safe values.
    """

    try:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, tuple):
            return list(value)

        return str(value)

    except Exception:
        return str(value)


def _gps_to_decimal(value, reference):
    """
    Convert EXIF GPS coordinates into decimal degrees.
    """

    try:
        degrees = float(value[0])
        minutes = float(value[1])
        seconds = float(value[2])

        decimal = degrees + (minutes / 60) + (seconds / 3600)

        if reference in ("S", "W"):
            decimal *= -1

        return decimal

    except Exception:
        return None


def extract_exif(image_path):
    """
    Extract useful EXIF information.
    """

    result = {
        "available": False,
        "fields": {},
        "gps": None,
    }

    try:
        with Image.open(image_path) as img:

            exif_data = img.getexif()

            if not exif_data:
                return result

            result["available"] = True

            for tag_id, value in exif_data.items():

                tag_name = ExifTags.TAGS.get(
                    tag_id,
                    str(tag_id)
                )

                result["fields"][tag_name] = _convert_exif_value(value)

            # ------------------------------------------------
            # GPS
            # ------------------------------------------------

            gps_info = exif_data.get(
                34853
            )

            if gps_info:

                gps = {}

                for key, value in gps_info.items():

                    gps_name = ExifTags.GPSTAGS.get(
                        key,
                        str(key)
                    )

                    gps[gps_name] = _convert_exif_value(value)

                latitude = gps.get("GPSLatitude")
                latitude_ref = gps.get("GPSLatitudeRef")

                longitude = gps.get("GPSLongitude")
                longitude_ref = gps.get("GPSLongitudeRef")

                if (
                    latitude
                    and latitude_ref
                    and longitude
                    and longitude_ref
                ):

                    lat = _gps_to_decimal(
                        latitude,
                        latitude_ref
                    )

                    lon = _gps_to_decimal(
                        longitude,
                        longitude_ref
                    )

                    if lat is not None and lon is not None:
                        result["gps"] = {
                            "latitude": lat,
                            "longitude": lon,
                        }

                if result["gps"] is None:
                    result["gps"] = {
                        "raw": gps
                    }

    except Exception as exc:
        result["error"] = str(exc)

    return result


# ============================================================
# IMAGE INFORMATION
# ============================================================

def get_image_information(image_path):
    """
    Collect general image information.
    """

    result = {}

    try:
        with Image.open(image_path) as img:

            result["format"] = img.format
            result["format_description"] = (
                Image.MIME.get(img.format, "Unknown")
            )

            result["width"] = img.width
            result["height"] = img.height
            result["mode"] = img.mode

            if img.width and img.height:

                result["aspect_ratio"] = round(
                    img.width / img.height,
                    4
                )

            result["animated"] = bool(
                getattr(img, "is_animated", False)
            )

            result["frames"] = getattr(
                img,
                "n_frames",
                1
            )

    except Exception as exc:
        result["error"] = str(exc)

    return result


# ============================================================
# OCR
# ============================================================

def extract_text_from_image(image_path):
    """
    Extract visible text using Tesseract OCR.

    OCR is optional.
    """

    result = {
        "available": pytesseract is not None,
        "text": "",
        "emails": [],
        "urls": [],
        "phone_numbers": [],
    }

    if pytesseract is None:
        result["error"] = (
            "pytesseract is not installed. "
            "Run: pip install pytesseract"
        )
        return result

    try:

        with Image.open(image_path) as img:

            text = pytesseract.image_to_string(
                img
            )

        result["text"] = text.strip()

        # ----------------------------------------------------
        # Emails
        # ----------------------------------------------------

        result["emails"] = sorted(
            set(
                re.findall(
                    r"\b[A-Za-z0-9._%+-]+@"
                    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                    text
                )
            )
        )

        # ----------------------------------------------------
        # URLs
        # ----------------------------------------------------

        result["urls"] = sorted(
            set(
                re.findall(
                    r"https?://[^\s]+",
                    text,
                    flags=re.IGNORECASE
                )
            )
        )

        # ----------------------------------------------------
        # Phone-like numbers
        # ----------------------------------------------------

        result["phone_numbers"] = sorted(
            set(
                re.findall(
                    r"(?<!\d)"
                    r"(?:\+?\d[\d\s().-]{7,}\d)"
                    r"(?!\d)",
                    text
                )
            )
        )

    except Exception as exc:
        result["error"] = str(exc)

    return result


# ============================================================
# IMAGE MANIPULATION INDICATORS
# ============================================================

def detect_metadata_indicators(exif_result):
    """
    Detect metadata that may indicate image processing.

    These are indicators only and do NOT prove manipulation.
    """

    indicators = []

    fields = exif_result.get(
        "fields",
        {}
    )

    software = str(
        fields.get(
            "Software",
            ""
        )
    ).lower()

    editing_keywords = [
        "photoshop",
        "gimp",
        "lightroom",
        "paint.net",
        "affinity",
        "snapseed",
        "canva",
        "pixlr",
        "illustrator",
        "after effects",
    ]

    for keyword in editing_keywords:

        if keyword in software:

            indicators.append({
                "type": "editing_software_metadata",
                "software": keyword,
                "description": (
                    "Image metadata contains an "
                    "editing-software indicator."
                ),
            })

            break

    if "GPS" in fields or exif_result.get("gps"):
        indicators.append({
            "type": "gps_metadata",
            "description": (
                "The image contains location-related metadata."
            ),
        })

    if "DateTimeOriginal" in fields:
        indicators.append({
            "type": "original_timestamp",
            "description": (
                "Original capture timestamp is present."
            ),
        })

    return indicators


# ============================================================
# IMAGE SIMILARITY
# ============================================================

def compare_images(image1_path, image2_path):
    """
    Compare two images using perceptual hashes.

    Returns Hamming distances and approximate similarity.
    """

    if imagehash is None:
        return {
            "error": (
                "ImageHash is not installed. "
                "Run: pip install ImageHash"
            )
        }

    try:

        with Image.open(image1_path) as img1:
            img1 = img1.convert("RGB")

            hashes1 = {
                "ahash": imagehash.average_hash(img1),
                "dhash": imagehash.dhash(img1),
                "phash": imagehash.phash(img1),
                "whash": imagehash.whash(img1),
            }

        with Image.open(image2_path) as img2:
            img2 = img2.convert("RGB")

            hashes2 = {
                "ahash": imagehash.average_hash(img2),
                "dhash": imagehash.dhash(img2),
                "phash": imagehash.phash(img2),
                "whash": imagehash.whash(img2),
            }

        result = {}

        similarities = []

        for name in hashes1:

            distance = (
                hashes1[name] - hashes2[name]
            )

            # 64-bit perceptual hashes.
            similarity = max(
                0,
                100 - ((distance / 64) * 100)
            )

            similarity = round(
                similarity,
                2
            )

            result[name] = {
                "hamming_distance": distance,
                "similarity_percent": similarity,
            }

            similarities.append(
                similarity
            )

        result["overall_similarity_percent"] = round(
            sum(similarities) / len(similarities),
            2
        )

        return result

    except Exception as exc:
        return {
            "error": str(exc)
        }


# ============================================================
# REVERSE SEARCH PROVIDER LINKS
# ============================================================

def generate_reverse_search_links(image_path=None):
    """
    Generate links to legitimate reverse-image-search services.

    Some services require the user to upload the image manually.
    This module does not bypass authentication, CAPTCHAs, or
    provider restrictions.
    """

    providers = {

        "Google Lens":
            "https://lens.google.com/",

        "Bing Visual Search":
            "https://www.bing.com/visualsearch",

        "Yandex Images":
            "https://yandex.com/images/",

        "TinEye":
            "https://tineye.com/",
    }

    return providers


# ============================================================
# IMAGE SEARCH QUERY GENERATION
# ============================================================

def generate_search_queries(ocr_result):
    """
    Generate useful search queries from OCR results.
    """

    queries = []

    text = ocr_result.get(
        "text",
        ""
    ).strip()

    if text:

        # Clean excessive whitespace.
        clean_text = re.sub(
            r"\s+",
            " ",
            text
        )

        if len(clean_text) > 200:
            clean_text = clean_text[:200]

        queries.append(clean_text)

    for email in ocr_result.get(
        "emails",
        []
    ):
        queries.append(email)

    for url in ocr_result.get(
        "urls",
        []
    ):
        queries.append(url)

    return queries


# ============================================================
# REVERSE IMAGE REPORT
# ============================================================

def analyze_image(image_path):
    """
    Complete reverse-image intelligence analysis.

    This is the main function your website can call.
    """

    report = {
        "scanner": {
            "name": "SecureMailScope Reverse Image Analyzer",
            "version": "1.0",
        },

        "timestamp": datetime.utcnow().isoformat()
        + "Z",

        "image": {},

        "hashes": {},

        "perceptual_hashes": {},

        "metadata": {},

        "ocr": {},

        "indicators": [],

        "search": {
            "providers": {},
            "queries": [],
        },

        "status": "failed",
    }

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    validation = validate_image_file(
        image_path
    )

    report["image"]["validation"] = validation

    if not validation["valid"]:
        report["error"] = validation["errors"]
        return report

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    report["image"]["information"] = (
        get_image_information(
            image_path
        )
    )

    # --------------------------------------------------------
    # CRYPTOGRAPHIC HASHES
    # --------------------------------------------------------

    try:
        report["hashes"] = (
            calculate_file_hashes(
                image_path
            )
        )

    except Exception as exc:
        report["hashes"] = {
            "error": str(exc)
        }

    # --------------------------------------------------------
    # PERCEPTUAL HASHES
    # --------------------------------------------------------

    report["perceptual_hashes"] = (
        calculate_perceptual_hashes(
            image_path
        )
    )

    # --------------------------------------------------------
    # EXIF
    # --------------------------------------------------------

    report["metadata"] = extract_exif(
        image_path
    )

    # --------------------------------------------------------
    # METADATA INDICATORS
    # --------------------------------------------------------

    report["indicators"] = (
        detect_metadata_indicators(
            report["metadata"]
        )
    )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    report["ocr"] = (
        extract_text_from_image(
            image_path
        )
    )

    # --------------------------------------------------------
    # SEARCH QUERIES
    # --------------------------------------------------------

    report["search"]["queries"] = (
        generate_search_queries(
            report["ocr"]
        )
    )

    # --------------------------------------------------------
    # REVERSE SEARCH PROVIDERS
    # --------------------------------------------------------

    report["search"]["providers"] = (
        generate_reverse_search_links(
            image_path
        )
    )

    # --------------------------------------------------------
    # GPS WARNING
    # --------------------------------------------------------

    if report["metadata"].get("gps"):

        report["indicators"].append({
            "type": "location_metadata",
            "severity": "HIGH",
            "description": (
                "GPS information was detected in "
                "the image metadata."
            ),
        })

    # --------------------------------------------------------
    # OCR WARNING
    # --------------------------------------------------------

    if report["ocr"].get("text"):

        report["indicators"].append({
            "type": "visible_text",
            "severity": "INFO",
            "description": (
                "Text was detected in the image "
                "and can be used for additional searching."
            ),
        })

    report["status"] = "completed"

    return report


# ============================================================
# JSON EXPORT
# ============================================================

def analyze_image_json(image_path):
    """
    Return the complete analysis as formatted JSON.
    """

    report = analyze_image(
        image_path
    )

    return json.dumps(
        report,
        indent=4,
        ensure_ascii=False,
        default=str
    )


# ============================================================
# SIMPLE CLI
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "SecureMailScope Reverse Image Analyzer"
        )
    )

    parser.add_argument(
        "image",
        help="Path to the image"
    )

    parser.add_argument(
        "--compare",
        help="Second image to compare"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON"
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # IMAGE COMPARISON
    # --------------------------------------------------------

    if args.compare:

        result = compare_images(
            args.image,
            args.compare
        )

        print(
            json.dumps(
                result,
                indent=4
            )
        )

    # --------------------------------------------------------
    # FULL ANALYSIS
    # --------------------------------------------------------

    else:

        report = analyze_image(
            args.image
        )

        if args.json:

            print(
                json.dumps(
                    report,
                    indent=4,
                    ensure_ascii=False,
                    default=str
                )
            )

        else:

            print("\n")
            print("=" * 60)
            print(
                "SECUREMAILSCOPE - REVERSE IMAGE ANALYSIS"
            )
            print("=" * 60)

            print(
                "\nStatus:",
                report["status"]
            )

            info = report["image"].get(
                "information",
                {}
            )

            print(
                "Format:",
                info.get("format")
            )

            print(
                "Dimensions:",
                f'{info.get("width")} x '
                f'{info.get("height")}'
            )

            hashes = report.get(
                "hashes",
                {}
            )

            print(
                "\nSHA-256:",
                hashes.get("sha256")
            )

            print(
                "\nPerceptual Hashes:"
            )

            for name, value in report.get(
                "perceptual_hashes",
                {}
            ).items():

                print(
                    f"  {name}: {value}"
                )

            print(
                "\nOCR:"
            )

            print(
                report["ocr"].get(
                    "text",
                    ""
                )[:1000]
            )

            print(
                "\nReverse Search Providers:"
            )

            for provider, url in report[
                "search"
            ][
                "providers"
            ].items():

                print(
                    f"  {provider}: {url}"
                )

            print(
                "\nIndicators:"
            )

            for indicator in report[
                "indicators"
            ]:

                print(
                    f"  [{indicator.get('severity', 'INFO')}] "
                    f"{indicator.get('description')}"
                )

            print("\n" + "=" * 60)
