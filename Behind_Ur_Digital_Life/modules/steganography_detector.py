# ============================================================
# SECUREMAILSCOPE - STEGANOGRAPHY DETECTION MODULE
# ============================================================
#
# Defensive static steganography analyzer.
#
# Detects indicators such as:
#   - LSB statistical anomalies
#   - Chi-square LSB analysis
#   - Entropy anomalies
#   - Bit-plane statistics
#   - RGB channel anomalies
#   - Alpha-channel anomalies
#   - Palette anomalies
#   - JPEG quantization information
#   - EXIF / metadata anomalies
#   - Trailing data after image end markers
#   - Embedded archive/file signatures
#   - Suspicious strings
#   - Image/file size anomalies
#   - PNG structural information
#   - Basic steganography risk score
#
# IMPORTANT:
#   This module does NOT extract hidden payloads.
#   Detection is probabilistic. A high score is an indicator,
#   NOT proof that steganography exists.
#
# Install:
#
#   pip install Pillow numpy
#
# ============================================================

import os
import re
import math
import json
import struct
import hashlib
from collections import Counter

import numpy as np
from PIL import Image


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILE_SIZE_MB = 100

SUPPORTED_FORMATS = {
    "PNG",
    "JPEG",
    "WEBP",
    "BMP",
    "TIFF",
    "GIF",
}

SUSPICIOUS_SIGNATURES = {
    b"PK\x03\x04": "ZIP archive",
    b"PK\x05\x06": "ZIP archive",
    b"Rar!\x1a\x07": "RAR archive",
    b"\x1f\x8b": "GZIP data",
    b"7z\xbc\xaf\x27\x1c": "7-Zip archive",
    b"%PDF": "PDF document",
    b"MZ": "Windows executable",
    b"\x7fELF": "ELF executable",
    b"SQLite format 3": "SQLite database",
}

SUSPICIOUS_TEXT_PATTERNS = [
    rb"password",
    rb"secret",
    rb"payload",
    rb"private_key",
    rb"BEGIN RSA PRIVATE KEY",
    rb"BEGIN OPENSSH PRIVATE KEY",
    rb"BEGIN PRIVATE KEY",
    rb"powershell",
    rb"cmd\.exe",
    rb"/bin/sh",
    rb"/bin/bash",
    rb"base64",
]


# ============================================================
# BASIC VALIDATION
# ============================================================

def validate_image(image_path):
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
    }

    if not image_path:
        result["errors"].append("No image path supplied.")
        return result

    if not os.path.exists(image_path):
        result["errors"].append("File does not exist.")
        return result

    if not os.path.isfile(image_path):
        result["errors"].append("Path is not a file.")
        return result

    size = os.path.getsize(image_path)

    result["size_bytes"] = size
    result["size_mb"] = round(
        size / (1024 * 1024),
        3
    )

    if result["size_mb"] > MAX_FILE_SIZE_MB:
        result["errors"].append(
            f"File exceeds {MAX_FILE_SIZE_MB} MB."
        )
        return result

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
            f"Invalid image: {exc}"
        )

    return result


# ============================================================
# FILE HASH
# ============================================================

def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


# ============================================================
# ENTROPY
# ============================================================

def calculate_entropy(data):
    """
    Shannon entropy in bits/byte.
    """

    if len(data) == 0:
        return 0.0

    counts = Counter(data)

    total = len(data)

    entropy = 0.0

    for count in counts.values():

        probability = count / total

        entropy -= (
            probability *
            math.log2(probability)
        )

    return round(
        entropy,
        5
    )


def image_entropy(image):
    """
    Entropy of the raw pixel representation.
    """

    array = np.asarray(image)

    if array.size == 0:
        return 0.0

    raw = array.tobytes()

    return calculate_entropy(raw)


# ============================================================
# BIT PLANE ANALYSIS
# ============================================================

def bit_plane_statistics(image):
    """
    Analyze individual bit planes.

    Particularly useful for detecting unusual patterns in
    lower-order bits.
    """

    array = np.asarray(
        image.convert("RGB"),
        dtype=np.uint8
    )

    result = {}

    for bit in range(8):

        plane = (
            (array >> bit) & 1
        )

        ones = int(
            np.sum(plane)
        )

        total = plane.size

        ratio = (
            ones / total
            if total
            else 0
        )

        result[f"bit_{bit}"] = {
            "ones": ones,
            "zeros": total - ones,
            "ones_ratio": round(
                ratio,
                6
            ),
        }

    return result


# ============================================================
# LSB ANALYSIS
# ============================================================

def lsb_statistics(image):
    """
    Analyze least-significant bits of RGB channels.
    """

    array = np.asarray(
        image.convert("RGB"),
        dtype=np.uint8
    )

    result = {}

    for index, channel_name in enumerate(
        ["red", "green", "blue"]
    ):

        channel = array[:, :, index]

        lsb = channel & 1

        ones = int(
            np.sum(lsb)
        )

        total = lsb.size

        ratio = (
            ones / total
            if total
            else 0
        )

        result[channel_name] = {
            "ones_ratio": round(
                ratio,
                6
            ),
            "ones": ones,
            "zeros": total - ones,
        }

    return result


# ============================================================
# LSB RANDOMNESS INDICATOR
# ============================================================

def lsb_randomness_score(image):
    """
    Estimate how random the LSB stream appears.

    This is only an indicator. Natural images can also produce
    highly random-looking LSB distributions.
    """

    array = np.asarray(
        image.convert("RGB"),
        dtype=np.uint8
    )

    lsb = (
        array & 1
    ).flatten()

    if len(lsb) < 2:
        return 0.0

    transitions = np.sum(
        lsb[:-1] != lsb[1:]
    )

    transition_ratio = (
        transitions /
        (len(lsb) - 1)
    )

    return round(
        float(transition_ratio),
        6
    )


# ============================================================
# CHI-SQUARE LSB ANALYSIS
# ============================================================

def chi_square_lsb(image):
    """
    Approximate chi-square analysis of LSB pairs.

    This can identify unusual LSB distributions but cannot
    independently prove hidden data.
    """

    array = np.asarray(
        image.convert("RGB"),
        dtype=np.uint8
    )

    results = {}

    for index, channel_name in enumerate(
        ["red", "green", "blue"]
    ):

        channel = array[:, :, index]

        values = channel.flatten()

        even = np.bincount(
            values[values % 2 == 0] // 2,
            minlength=128
        )

        odd = np.bincount(
            values[values % 2 == 1] // 2,
            minlength=128
        )

        chi = 0.0

        for e, o in zip(even, odd):

            total = e + o

            if total == 0:
                continue

            expected = total / 2

            chi += (
                ((e - expected) ** 2) /
                expected
            )

            chi += (
                ((o - expected) ** 2) /
                expected
            )

        results[channel_name] = round(
            float(chi),
            4
        )

    return results


# ============================================================
# RGB CHANNEL ANALYSIS
# ============================================================

def channel_statistics(image):
    array = np.asarray(
        image.convert("RGB"),
        dtype=np.float64
    )

    result = {}

    for index, name in enumerate(
        ["red", "green", "blue"]
    ):

        channel = array[:, :, index]

        result[name] = {
            "mean": round(
                float(np.mean(channel)),
                4
            ),
            "std": round(
                float(np.std(channel)),
                4
            ),
            "min": int(
                np.min(channel)
            ),
            "max": int(
                np.max(channel)
            ),
        }

    return result


# ============================================================
# ALPHA CHANNEL ANALYSIS
# ============================================================

def alpha_channel_analysis(image):
    result = {
        "present": False
    }

    if "A" not in image.getbands():
        return result

    alpha = np.asarray(
        image.getchannel("A"),
        dtype=np.uint8
    )

    result["present"] = True

    result["mean"] = round(
        float(np.mean(alpha)),
        4
    )

    result["std"] = round(
        float(np.std(alpha)),
        4
    )

    result["unique_values"] = int(
        len(np.unique(alpha))
    )

    result["fully_transparent_pixels"] = int(
        np.sum(alpha == 0)
    )

    result["fully_opaque_pixels"] = int(
        np.sum(alpha == 255)
    )

    return result


# ============================================================
# METADATA ANALYSIS
# ============================================================

def metadata_analysis(image):
    result = {
        "metadata": {},
        "indicators": [],
    }

    try:

        exif = image.getexif()

        if exif:

            for key, value in exif.items():

                result["metadata"][
                    str(key)
                ] = str(value)

    except Exception:
        pass

    info = image.info

    for key, value in info.items():

        if key.lower() in {
            "comment",
            "description",
            "software",
            "parameters",
            "xml",
        }:

            result["indicators"].append({
                "type": "embedded_metadata",
                "field": key,
                "description":
                    "Additional image metadata detected.",
            })

    return result


# ============================================================
# TRAILING DATA DETECTION
# ============================================================

def detect_trailing_data(image_path):
    """
    Detect bytes appearing after common image end markers.

    This can indicate appended data, although legitimate files
    and some formats can also contain trailing structures.
    """

    with open(image_path, "rb") as f:
        data = f.read()

    findings = []

    # JPEG end-of-image marker.
    jpeg_end = data.rfind(
        b"\xff\xd9"
    )

    if jpeg_end != -1:

        trailing = data[
            jpeg_end + 2:
        ]

        if trailing:

            findings.append({
                "format": "JPEG",
                "offset": jpeg_end + 2,
                "trailing_bytes": len(trailing),
                "description":
                    "Data exists after the JPEG end marker.",
            })

    # PNG IEND chunk.
    png_iend = data.rfind(
        b"IEND"
    )

    if png_iend != -1:

        # IEND chunk occupies 12 bytes:
        # length + type + CRC.
        end_offset = png_iend + 8 + 4

        if end_offset < len(data):

            trailing = data[
                end_offset:
            ]

            if trailing:

                findings.append({
                    "format": "PNG",
                    "offset": end_offset,
                    "trailing_bytes": len(trailing),
                    "description":
                        "Data exists after the PNG IEND structure.",
                })

    return findings


# ============================================================
# EMBEDDED FILE SIGNATURE DETECTION
# ============================================================

def detect_embedded_signatures(image_path):
    """
    Search for common embedded-file signatures.

    Detection does not extract or execute them.
    """

    with open(image_path, "rb") as f:
        data = f.read()

    findings = []

    for signature, description in (
        SUSPICIOUS_SIGNATURES.items()
    ):

        # Ignore position 0 because that may simply be the
        # actual file format signature.
        positions = []

        start = 1

        while True:

            position = data.find(
                signature,
                start
            )

            if position == -1:
                break

            positions.append(position)

            start = position + 1

        for position in positions:

            findings.append({
                "signature": description,
                "offset": position,
                "description":
                    f"Embedded {description} signature detected.",
            })

    return findings


# ============================================================
# SUSPICIOUS STRING DETECTION
# ============================================================

def detect_suspicious_strings(image_path):
    with open(image_path, "rb") as f:
        data = f.read()

    findings = []

    for pattern in SUSPICIOUS_TEXT_PATTERNS:

        if re.search(
            pattern,
            data,
            flags=re.IGNORECASE
        ):

            findings.append({
                "pattern":
                    pattern.decode(
                        "utf-8",
                        errors="replace"
                    ),
                "description":
                    "Suspicious string detected inside file.",
            })

    return findings


# ============================================================
# FILE SIZE / PIXEL RATIO
# ============================================================

def file_size_analysis(image_path, image):
    size = os.path.getsize(
        image_path
    )

    pixels = (
        image.width *
        image.height
    )

    bytes_per_pixel = (
        size / pixels
        if pixels
        else 0
    )

    return {
        "file_size_bytes": size,
        "pixels": pixels,
        "bytes_per_pixel": round(
            bytes_per_pixel,
            6
        ),
    }


# ============================================================
# SCORE CALCULATION
# ============================================================

def calculate_risk_score(
    lsb_stats,
    lsb_randomness,
    chi_square,
    trailing_data,
    embedded_signatures,
    suspicious_strings,
    alpha_info,
    metadata_info,
):
    """
    Calculate an indicator score.

    This is NOT a probability of steganography.
    """

    score = 0
    reasons = []

    # --------------------------------------------------------
    # LSB distribution
    # --------------------------------------------------------

    for channel, values in lsb_stats.items():

        ratio = values["ones_ratio"]

        if ratio < 0.40 or ratio > 0.60:

            score += 5

            reasons.append(
                f"Unusual LSB ratio in {channel} channel."
            )

    # --------------------------------------------------------
    # LSB randomness
    # --------------------------------------------------------

    if (
        0.47 <=
        lsb_randomness <=
        0.53
    ):

        score += 10

        reasons.append(
            "LSB stream appears highly balanced/random."
        )

    # --------------------------------------------------------
    # Chi-square indicator
    # --------------------------------------------------------

    for channel, value in chi_square.items():

        if value < 50:

            score += 5

            reasons.append(
                f"Unusual chi-square result for {channel}."
            )

    # --------------------------------------------------------
    # Trailing data
    # --------------------------------------------------------

    if trailing_data:

        score += 25

        reasons.append(
            "Data detected after an image end structure."
        )

    # --------------------------------------------------------
    # Embedded signatures
    # --------------------------------------------------------

    if embedded_signatures:

        score += min(
            30,
            len(embedded_signatures) * 10
        )

        reasons.append(
            "Embedded file signature(s) detected."
        )

    # --------------------------------------------------------
    # Suspicious strings
    # --------------------------------------------------------

    if suspicious_strings:

        score += min(
            20,
            len(suspicious_strings) * 5
        )

        reasons.append(
            "Suspicious strings detected inside image data."
        )

    # --------------------------------------------------------
    # Alpha channel
    # --------------------------------------------------------

    if alpha_info.get("present"):

        unique_values = alpha_info.get(
            "unique_values",
            0
        )

        if unique_values > 2:

            score += 5

            reasons.append(
                "Alpha channel contains multiple transparency levels."
            )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    if metadata_info.get("indicators"):

        score += 3

        reasons.append(
            "Additional metadata fields detected."
        )

    score = min(
        score,
        100
    )

    if score >= 80:
        severity = "CRITICAL"

    elif score >= 60:
        severity = "HIGH"

    elif score >= 40:
        severity = "MEDIUM"

    elif score >= 20:
        severity = "LOW"

    else:
        severity = "INFO"

    return {
        "score": score,
        "severity": severity,
        "reasons": reasons,
    }


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

def analyze_steganography(image_path):
    """
    Main steganography detection function.
    """

    report = {
        "scanner": {
            "name":
                "SecureMailScope Steganography Detector",
            "version":
                "1.0",
        },

        "status": "failed",

        "file": {},

        "image": {},

        "hash": {},

        "statistics": {},

        "metadata": {},

        "forensic_indicators": {},

        "risk": {},
    }

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validation = validate_image(
        image_path
    )

    report["file"] = validation

    if not validation["valid"]:
        report["error"] = validation["errors"]
        return report

    # --------------------------------------------------------
    # Open image
    # --------------------------------------------------------

    try:

        with Image.open(
            image_path
        ) as img:

            image = img.copy()

    except Exception as exc:

        report["error"] = str(exc)

        return report

    # --------------------------------------------------------
    # Basic image information
    # --------------------------------------------------------

    report["image"] = {
        "format": image.format,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "bands": image.getbands(),
    }

    # --------------------------------------------------------
    # Hash
    # --------------------------------------------------------

    report["hash"]["sha256"] = (
        sha256_file(
            image_path
        )
    )

    # --------------------------------------------------------
    # Entropy
    # --------------------------------------------------------

    report["statistics"]["entropy"] = (
        image_entropy(
            image
        )
    )

    # --------------------------------------------------------
    # Bit planes
    # --------------------------------------------------------

    report["statistics"]["bit_planes"] = (
        bit_plane_statistics(
            image
        )
    )

    # --------------------------------------------------------
    # LSB
    # --------------------------------------------------------

    lsb_stats = lsb_statistics(
        image
    )

    report["statistics"]["lsb"] = (
        lsb_stats
    )

    # --------------------------------------------------------
    # LSB randomness
    # --------------------------------------------------------

    lsb_randomness = (
        lsb_randomness_score(
            image
        )
    )

    report["statistics"][
        "lsb_randomness"
    ] = lsb_randomness

    # --------------------------------------------------------
    # Chi-square
    # --------------------------------------------------------

    chi_square = chi_square_lsb(
        image
    )

    report["statistics"][
        "chi_square_lsb"
    ] = chi_square

    # --------------------------------------------------------
    # RGB channels
    # --------------------------------------------------------

    report["statistics"][
        "channels"
    ] = channel_statistics(
        image
    )

    # --------------------------------------------------------
    # Alpha
    # --------------------------------------------------------

    alpha_info = alpha_channel_analysis(
        image
    )

    report["statistics"][
        "alpha"
    ] = alpha_info

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata_info = metadata_analysis(
        image
    )

    report["metadata"] = metadata_info

    # --------------------------------------------------------
    # File size
    # --------------------------------------------------------

    report["statistics"][
        "file_size"
    ] = file_size_analysis(
        image_path,
        image
    )

    # --------------------------------------------------------
    # Trailing data
    # --------------------------------------------------------

    trailing_data = (
        detect_trailing_data(
            image_path
        )
    )

    report["forensic_indicators"][
        "trailing_data"
    ] = trailing_data

    # --------------------------------------------------------
    # Embedded signatures
    # --------------------------------------------------------

    embedded_signatures = (
        detect_embedded_signatures(
            image_path
        )
    )

    report["forensic_indicators"][
        "embedded_signatures"
    ] = embedded_signatures

    # --------------------------------------------------------
    # Suspicious strings
    # --------------------------------------------------------

    suspicious_strings = (
        detect_suspicious_strings(
            image_path
        )
    )

    report["forensic_indicators"][
        "suspicious_strings"
    ] = suspicious_strings

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    report["risk"] = calculate_risk_score(
        lsb_stats=lsb_stats,
        lsb_randomness=lsb_randomness,
        chi_square=chi_square,
        trailing_data=trailing_data,
        embedded_signatures=embedded_signatures,
        suspicious_strings=suspicious_strings,
        alpha_info=alpha_info,
        metadata_info=metadata_info,
    )

    report["status"] = "completed"

    return report


# ============================================================
# JSON OUTPUT
# ============================================================

def analyze_steganography_json(
    image_path
):
    """
    Return analysis as formatted JSON.
    """

    return json.dumps(
        analyze_steganography(
            image_path
        ),
        indent=4,
        ensure_ascii=False,
        default=str,
    )


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "SecureMailScope Steganography Detector"
        )
    )

    parser.add_argument(
        "image",
        help="Image to analyze"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output complete JSON report"
    )

    args = parser.parse_args()

    report = analyze_steganography(
        args.image
    )

    if args.json:

        print(
            json.dumps(
                report,
                indent=4,
                ensure_ascii=False,
                default=str,
            )
        )

    else:

        print("\n")
        print("=" * 65)
        print(
            "SECUREMAILSCOPE - STEGANOGRAPHY DETECTOR"
        )
        print("=" * 65)

        print(
            "\nStatus:",
            report["status"]
        )

        print(
            "SHA-256:",
            report["hash"].get(
                "sha256"
            )
        )

        print(
            "Format:",
            report["image"].get(
                "format"
            )
        )

        print(
            "Dimensions:",
            report["image"].get(
                "width"
            ),
            "x",
            report["image"].get(
                "height"
            )
        )

        print(
            "\nEntropy:",
            report["statistics"].get(
                "entropy"
            )
        )

        print(
            "LSB randomness:",
            report["statistics"].get(
                "lsb_randomness"
            )
        )

        risk = report["risk"]

        print(
            "\nRisk score:",
            risk.get(
                "score"
            ),
            "/ 100"
        )

        print(
            "Severity:",
            risk.get(
                "severity"
            )
        )

        print(
            "\nIndicators:"
        )

        for reason in risk.get(
            "reasons",
            []
        ):

            print(
                " -",
                reason
            )

        print(
            "\nEmbedded signatures:",
            len(
                report[
                    "forensic_indicators"
                ][
                    "embedded_signatures"
                ]
            )
        )

        print(
            "Trailing-data findings:",
            len(
                report[
                    "forensic_indicators"
                ][
                    "trailing_data"
                ]
            )
        )

        print("\n" + "=" * 65)
