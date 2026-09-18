import io
import logging
from typing import Tuple
from PIL import Image, ImageEnhance, ExifTags

from core.logging import get_logger
from .schemas import PreprocessedImageMeta

logger = get_logger("vision.preprocessor")

def preprocess_challan_image(image_bytes: bytes) -> Tuple[bytes, bytes, PreprocessedImageMeta]:
    """
    Stage A: Preprocesses the raw challan image.
    Applies EXIF orientation, contrast enhancement, resizing, and grayscale conversion.
    """
    logger.info("[preprocess] Starting image preprocessing")
    
    img = Image.open(io.BytesIO(image_bytes))
    original_format = img.format or "JPEG"
    original_dimensions = img.size
    
    was_rotated = False
    contrast_enhanced = False
    grayscale_variant_created = False
    
    # Auto-orient based on EXIF
    try:
        exif = img.getexif()
        if exif is not None:
            orientation_key = None
            for key, val in ExifTags.TAGS.items():
                if val == 'Orientation':
                    orientation_key = key
                    break
            
            if orientation_key in exif:
                orientation = exif[orientation_key]
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                    was_rotated = True
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                    was_rotated = True
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
                    was_rotated = True
    except Exception as e:
        logger.warning(f"[preprocess] EXIF rotation failed: {e}")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    contrast_enhanced = True
    
    # Resize if max dimension > 1600px
    max_dim = 1600
    if img.size[0] > max_dim or img.size[1] > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    
    resized_to = img.size
    
    # Ensure RGB for JPEG conversion
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Save optimized color image
    color_bytes_io = io.BytesIO()
    img.save(color_bytes_io, format="JPEG", quality=85)
    color_bytes = color_bytes_io.getvalue()
    
    # Generate grayscale variant
    gray_img = img.convert("L")
    gray_bytes_io = io.BytesIO()
    gray_img.save(gray_bytes_io, format="JPEG", quality=85)
    grayscale_bytes = gray_bytes_io.getvalue()
    grayscale_variant_created = True
    
    meta = PreprocessedImageMeta(
        original_format=original_format,
        original_dimensions=original_dimensions,
        was_rotated=was_rotated,
        contrast_enhanced=contrast_enhanced,
        resized_to=resized_to,
        grayscale_variant_created=grayscale_variant_created
    )
    
    logger.info(f"[preprocess] Preprocessing complete. Original: {original_dimensions}, Resized: {resized_to}, Rotated: {was_rotated}")
    return color_bytes, grayscale_bytes, meta
