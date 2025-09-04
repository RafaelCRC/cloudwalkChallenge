"""OCR functionality for image text extraction."""

import os
import tempfile
from typing import Optional, Dict, Any
from PIL import Image
import pytesseract
import structlog
import aiofiles
from .monitoring import OCR_PROCESSING_TIME

from .config import settings

logger = structlog.get_logger(__name__)


class OCRProcessor:
    """Secure OCR processor for extracting text from images."""
    
    def __init__(self):
        self.languages = settings.ocr_languages
        self.confidence_threshold = settings.ocr_confidence_threshold
    
    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process image with OCR and return extracted text with confidence.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict containing extracted text and confidence score
        """
        try:
            # Validate image file
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Security: Validate file size (max 10MB)
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:
                raise ValueError("Image file too large (max 10MB)")
            
            # Open and validate image
            with Image.open(image_path) as img:
                # Security: Validate image dimensions
                if img.width > 4000 or img.height > 4000:
                    raise ValueError("Image dimensions too large")
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Perform OCR with confidence data
                with OCR_PROCESSING_TIME.time():
                    ocr_data = pytesseract.image_to_data(
                        img,
                        lang=self.languages,
                        output_type=pytesseract.Output.DICT,
                        config='--psm 6'  # Uniform block of text
                    )
                
                # Extract text and calculate confidence
                text_parts = []
                confidences = []
                
                for i, conf in enumerate(ocr_data['conf']):
                    if int(conf) > self.confidence_threshold:
                        word = ocr_data['text'][i].strip()
                        if word:
                            text_parts.append(word)
                            confidences.append(int(conf))
                
                extracted_text = ' '.join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                logger.info(
                    "OCR processing completed",
                    text_length=len(extracted_text),
                    confidence=avg_confidence,
                    words_extracted=len(text_parts)
                )
                
                return {
                    'text': extracted_text,
                    'confidence': avg_confidence,
                    'word_count': len(text_parts),
                    'success': True
                }
                
        except Exception as e:
            logger.error("OCR processing failed", error=str(e), image_path=image_path)
            return {
                'text': '',
                'confidence': 0,
                'word_count': 0,
                'success': False,
                'error': str(e)
            }
    
    async def process_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Process image from bytes data.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dict containing extracted text and confidence score
        """
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
            
            try:
                # Write bytes to temporary file
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(image_bytes)
                
                # Process the temporary file
                result = await self.process_image(temp_path)
                
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except OSError:
                    logger.warning("Failed to cleanup temporary file", path=temp_path)
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if too small (improve OCR accuracy)
            width, height = image.size
            if width < 300 or height < 300:
                scale_factor = max(300 / width, 300 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.error("Image preprocessing failed", error=str(e))
            return image


# Global OCR processor instance
ocr_processor = OCRProcessor()

