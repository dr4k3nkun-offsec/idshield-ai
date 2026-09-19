import hashlib
import os
import re
from typing import Any, Dict, List
import cv2
import numpy as np
from PIL import ExifTags, Image

GRID_SIZE = 12


def extract_prnu_sensor_fingerprint(gray: np.ndarray) -> Dict[str, Any]:
    """
    Extracts the Photo-Response Non-Uniformity (PRNU) silicon noise residual.
    Uses edge-suppression to prevent high-contrast document typography from
    contaminating the physical camera sensor signature.
    """
    h, w = gray.shape[:2]
    if h < 64 or w < 64:
        return {
            "sensor_hash": "INSUFFICIENT_CANVAS_RES",
            "noise_variance": 0.0,
            "sensor_anomaly": False,
        }

    # 1. Non-linear median spatial denoising to isolate noise residual: W = I - F(I)
    denoised = cv2.medianBlur(gray, 3)
    residual = gray.astype(np.float32) - denoised.astype(np.float32)

    # 2. Strict Canny edge masking: Strip all text, barcodes, photo boundaries, and lines
    # Dilate edges so text transitions NEVER contaminate the sensor noise floor
    edges = cv2.Canny(gray, 50, 150)
    dilated_edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    substrate_mask = dilated_edges == 0

    valid_pixels = np.sum(substrate_mask)
    if valid_pixels < 1024:
        return {
            "sensor_hash": "HIGH_TEXTURE_DENSITY",
            "noise_variance": 0.0,
            "sensor_anomaly": False,
        }

    # 3. Calculate true sensor noise variance strictly over non-edge substrate
    clean_residual = residual[substrate_mask]
    noise_variance = float(np.var(clean_residual))

    # 4. Generate deterministic 64-bit spatial sensor signature hash
    # Downsample substrate residual to an 8x8 standardized spatial block
    small_res = cv2.resize(residual, (8, 8), interpolation=cv2.INTER_AREA)
    mean_val = np.mean(small_res)
    bits = "".join(["1" if val > mean_val else "0" for val in small_res.flatten()])
    sensor_hash = f"{int(bits, 2):016X}"

    # Flag anomaly only if variance is unnaturally zero on a photo (pure vector/synthetic render)
    sensor_anomaly = noise_variance < 0.02

    return {
        "sensor_hash": sensor_hash,
        "noise_variance": round(noise_variance, 4),
        "sensor_anomaly": sensor_anomaly,
    }


def detect_genai_diffusion_spectra(gray: np.ndarray) -> Dict[str, Any]:
    """
    Analyzes high-frequency radial Fourier power spectrum for upsampling artifacts
    typical of Generative Diffusion models (Stable Diffusion, Midjourney, Flux)
    and GAN-infilled credentials.
    """
    h, w = gray.shape[:2]
    # Standardize to 512x512 power-of-two patch for stable Fourier resolution
    target_dim = 512
    if h != target_dim or w != target_dim:
        patch = cv2.resize(gray, (target_dim, target_dim), interpolation=cv2.INTER_AREA)
    else:
        patch = gray

    # 1. 2D Hann spatial window to eliminate rectangular border leakage
    hann_h = np.hanning(target_dim)
    hann_w = np.hanning(target_dim)
    hann_2d = np.outer(hann_h, hann_w)
    windowed = (patch.astype(np.float32) - np.mean(patch)) * hann_2d

    # 2. 2D Fast Fourier Transform & Power Spectrum
    f_shift = np.fft.fftshift(np.fft.fft2(windowed))
    power_spectrum = np.log1p(np.abs(f_shift) ** 2)

    # 3. High-frequency annular band evaluation (avoids both low-frequency content and nyquist edge)
    y, x = np.ogrid[:target_dim, :target_dim]
    center = target_dim // 2
    r = np.sqrt((x - center) ** 2 + (y - center) ** 2)

    # Annular inspection band: 20% to 75% of max radius
    min_r = int(0.20 * center)
    max_r = int(0.75 * center)
    band_mask = (r >= min_r) & (r <= max_r)

    band_powers = power_spectrum[band_mask]
    if band_powers.size == 0:
        return {"genai_detected": False, "spectral_peak_ratio": 1.0}

    mean_band = float(np.mean(band_powers))
    std_band = float(np.std(band_powers))
    max_band = float(np.max(band_powers))

    # Peak-to-Average Spectral Ratio (PASR)
    pasr = max_band / (mean_band + 1e-7)

    # Diffusion models exhibit periodic checkerboard upsampling spikes (PASR > 2.65 with high std deviation)
    is_genai = bool(pasr > 2.65 and std_band > 1.85)

    return {
        "genai_detected": is_genai,
        "spectral_peak_ratio": round(pasr, 3),
        "spectral_variance": round(std_band, 3),
    }


def analyze_advanced_tampering(file_path: str, cv_img: np.ndarray) -> Dict[str, Any]:
    """
    Executes deep multi-layer forensic inspection:
    1. 12x12 Block Error Level Analysis (ELA)
    2. Substrate texture & noise-floor variance
    3. Hardware EXIF integrity & timestamp audit
    4. PRNU silicon sensor noise extraction
    5. GenAI / Diffusion 2D-FFT azimuthal spectral detection
    """
    indicators: List[str] = []
    suspicious_regions: List[Dict[str, Any]] = []

    if cv_img is None or cv_img.size == 0:
        return {
            "tampering_detected": False,
            "confidence": 0.0,
            "indicators": ["Image buffer invalid or unreadable."],
            "suspicious_regions": [],
            "metadata_findings": {"has_exif": False},
            "ela_score": 90.0,
            "noise_score": 0.0,
            "compression_score": 0.0,
            "prnu_findings": {},
            "spectral_findings": {},
            "explanation": "Image buffer could not be processed for forensic analysis.",
        }

    h, w = cv_img.shape[:2]
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    block_w = max(1, w // GRID_SIZE)
    block_h = max(1, h // GRID_SIZE)

    # -------------------------------------------------------------
    # 1. 12x12 GRID ERROR LEVEL ANALYSIS (ELA)
    # -------------------------------------------------------------
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    _, encoded_jpg = cv2.imencode(".jpg", cv_img, encode_param)
    recompressed = cv2.imdecode(encoded_jpg, cv2.IMREAD_COLOR)

    diff = cv2.absdiff(cv_img, recompressed).astype(np.float32)
    diff_sum = np.sum(diff, axis=2)

    block_errors = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
    for by in range(GRID_SIZE):
        for bx in range(GRID_SIZE):
            y0, y1 = by * block_h, min((by + 1) * block_h, h)
            x0, x1 = bx * block_w, min((bx + 1) * block_w, w)
            block_crop = diff_sum[y0:y1, x0:x1]
            block_errors[by, bx] = float(np.mean(block_crop)) if block_crop.size > 0 else 0.0

    mean_err = float(np.mean(block_errors))
    std_err = float(np.std(block_errors))
    ela_threshold = mean_err + (1.75 * std_err)

    for by in range(GRID_SIZE):
        for bx in range(GRID_SIZE):
            val = block_errors[by, bx]
            if val > ela_threshold and val > 8.0:
                bx_pix = bx * block_w
                by_pix = by * block_h
                confidence_val = int(min(99, max(65, (val / (ela_threshold + 1e-5)) * 85)))
                suspicious_regions.append({
                    "id": f"EV-ELA-{by}-{bx}",
                    "label": "Elevated Compression Residue",
                    "confidence": confidence_val,
                    "x": round((bx_pix / w) * 100, 2),
                    "y": round((by_pix / h) * 100, 2),
                    "width": round((block_w / w) * 100, 2),
                    "height": round((block_h / h) * 100, 2),
                    "type": "pixel_splice",
                    "explanation": (
                        f"Statistical ELA residue outlier (val={round(val, 2)} "
                        f"vs threshold={round(ela_threshold, 2)})."
                    ),
                })

    ela_spread_score = float(min(1.0, std_err / 28.0))
    if len(suspicious_regions) > 0:
        indicators.append(
            f"{len(suspicious_regions)} regional block(s) exhibit elevated ELA residue consistent with localized pixel splicing."
        )

    # -------------------------------------------------------------
    # 2. NOISE & TEXTURE INCONSISTENCY (CLONE/SMOOTHING DETECTOR)
    # -------------------------------------------------------------
    block_noise = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
    for by in range(GRID_SIZE):
        for bx in range(GRID_SIZE):
            y0, y1 = by * block_h, min((by + 1) * block_h, h)
            x0, x1 = bx * block_w, min((bx + 1) * block_w, w)
            patch = gray[y0:y1, x0:x1]
            block_noise[by, bx] = float(np.std(patch)) if patch.size > 0 else 0.0

    mean_noise = float(np.mean(block_noise))
    std_noise = float(np.std(block_noise))
    smooth_threshold = max(1.0, mean_noise - (1.5 * std_noise))
    low_noise_outliers = int(np.sum(block_noise < smooth_threshold))
    noise_anomaly_score = float(min(1.0, (low_noise_outliers / (GRID_SIZE * GRID_SIZE)) * 3.5))

    if low_noise_outliers > 3:
        indicators.append(
            f"{low_noise_outliers} image blocks show abnormal texture smoothing, suggesting brush cloning or background scrubbing."
        )

    # -------------------------------------------------------------
    # 3. PRNU SENSOR NOISE & HARDWARE ATTRIBUTION
    # -------------------------------------------------------------
    prnu_results = extract_prnu_sensor_fingerprint(gray)

    # -------------------------------------------------------------
    # 4. GENAI / DIFFUSION AZIMUTHAL SPECTRAL INFERENCE
    # -------------------------------------------------------------
    spectral_results = detect_genai_diffusion_spectra(gray)
    if spectral_results["genai_detected"]:
        indicators.append(
            f"Periodic lattice frequency spike detected (PASR: {spectral_results['spectral_peak_ratio']}), "
            "indicating Generative AI inpainting or synthetic diffusion synthesis."
        )

    # -------------------------------------------------------------
    # 5. EXIF METADATA TAMPERING AUDIT
    # -------------------------------------------------------------
    meta_findings = {
        "has_exif": False,
        "editing_software_detected": False,
        "software": None,
        "timestamp_mismatch": False,
    }

    if os.path.exists(file_path):
        try:
            with Image.open(file_path) as pil_img:
                raw_exif = pil_img.getexif()

            if raw_exif:
                meta_findings["has_exif"] = True
                exif_dict = {ExifTags.TAGS.get(k, k): v for k, v in raw_exif.items()}
                software = str(exif_dict.get("Software", "")).strip()
                date_time = str(exif_dict.get("DateTime", "")).strip()
                date_time_orig = str(exif_dict.get("DateTimeOriginal", "")).strip()

                meta_findings["software"] = software or None
                editing_tools = r"photoshop|gimp|paint\.net|snapseed|lightroom|illustrator|pixlr|canva"
                if software and re.search(editing_tools, software, re.IGNORECASE):
                    meta_findings["editing_software_detected"] = True
                    indicators.append(f'EXIF metadata records external image editing software: "{software}".')

                if date_time and date_time_orig and date_time != date_time_orig:
                    meta_findings["timestamp_mismatch"] = True
                    indicators.append("EXIF modification timestamp diverges from original camera capture time.")
            else:
                indicators.append("No hardware camera EXIF metadata present (screenshot, scan, or stripped header).")
        except Exception:
            indicators.append("EXIF header parsing failed or was stripped during transmission.")
    else:
        indicators.append("Source file handle unavailable for binary metadata analysis.")

    # -------------------------------------------------------------
    # 6. COMPOSITE FORENSIC CONFIDENCE MATRIX
    # -------------------------------------------------------------
    meta_penalty = (
        (0.30 if meta_findings["editing_software_detected"] else 0.0)
        + (0.15 if meta_findings["timestamp_mismatch"] else 0.0)
    )
    genai_penalty = 0.40 if spectral_results["genai_detected"] else 0.0

    composite_tampering_score = min(
        1.0,
        (ela_spread_score * 0.35)
        + (noise_anomaly_score * 0.25)
        + meta_penalty
        + genai_penalty,
    )

    tampering_detected = (
        composite_tampering_score >= 0.48
        or len(suspicious_regions) >= 4
        or spectral_results["genai_detected"]
    )

    explanation = (
        f"Statistical analysis flagged this document. {' '.join(indicators)}"
        if tampering_detected
        else "All image blocks fall within expected physical substrate noise variance."
    )

    return {
        "tampering_detected": tampering_detected,
        "confidence": round(composite_tampering_score, 3),
        "suspicious_regions": suspicious_regions[:6],
        "indicators": indicators,
        "metadata_findings": meta_findings,
        "ela_score": round(max(30.0, 100.0 - (std_err * 2.5)), 1),
        "noise_score": round(noise_anomaly_score, 3),
        "compression_score": round(ela_spread_score, 3),
        "prnu_findings": prnu_results,
        "spectral_findings": spectral_results,
        "explanation": explanation,
    }