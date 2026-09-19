import cv2
import numpy as np
import pytesseract

def apply_regulatory_mask(image_bgr: np.ndarray, doc_type: str) -> np.ndarray:
    """
    Scans the visual canvas for 12-digit identity patterns and applies
    permanent solid black redaction rectangles over the initial 8 digits
    prior to disk storage. Handles both single cards and composite front/back sheets.
    """
    if doc_type != "Aadhaar" or image_bgr is None:
        return image_bgr

    processed_img = image_bgr.copy()
    
    try:
        # Extract word-level bounding boxes and spatial coordinates
        ocr_data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
        n_boxes = len(ocr_data['text'])

        i = 0
        while i < n_boxes:
            w1 = ocr_data['text'][i].strip()

            # Case A: Number is grouped into 3 separate 4-digit blocks (e.g., "XXXX XXXX 1234")
            if i <= n_boxes - 3:
                w2 = ocr_data['text'][i + 1].strip()
                w3 = ocr_data['text'][i + 2].strip()

                if (len(w1) == 4 and w1.isdigit() and 
                    len(w2) == 4 and w2.isdigit() and 
                    len(w3) == 4 and w3.isdigit()):
                    
                    y1 = ocr_data['top'][i]
                    y2 = ocr_data['top'][i + 1]
                    y3 = ocr_data['top'][i + 2]

                    # Ensure all 3 chunks reside on the same horizontal baseline
                    if abs(y1 - y2) <= 15 and abs(y2 - y3) <= 15:
                        x1, width1, height1 = ocr_data['left'][i], ocr_data['width'][i], ocr_data['height'][i]
                        x2, width2, height2 = ocr_data['left'][i + 1], ocr_data['width'][i + 1], ocr_data['height'][i + 1]

                        # Mask first chunk (first 4 digits)
                        cv2.rectangle(processed_img, (x1 - 2, y1 - 2), (x1 + width1 + 2, y1 + height1 + 2), (0, 0, 0), -1)
                        # Mask second chunk (next 4 digits)
                        cv2.rectangle(processed_img, (x2 - 2, y2 - 2), (x2 + width2 + 2, y2 + height2 + 2), (0, 0, 0), -1)

                        # Skip forward past matched group and continue scanning remaining canvas
                        i += 3
                        continue

            # Case B: Number is parsed as an unspaced 12-digit continuous sequence
            clean_token = ''.join(filter(str.isdigit, w1))
            if len(clean_token) == 12:
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]

                # Mask initial 8 digits (two-thirds of word width)
                mask_w = int(w * (8.0 / 12.0))
                cv2.rectangle(processed_img, (x - 2, y - 2), (x + mask_w, y + h + 2), (0, 0, 0), -1)

            i += 1

    except Exception as e:
        print(f"[WARN] Regulatory auto-masking bypass: {e}")

    return processed_img