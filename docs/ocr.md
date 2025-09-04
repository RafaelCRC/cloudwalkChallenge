# 🔍 OCR (Optical Character Recognition)

Text extraction from images using Tesseract OCR engine.

## Overview

The `OCRProcessor` class extracts text from images sent in Telegram messages:

- **Image Processing** - Handles photos and document images
- **Text Extraction** - Uses Tesseract OCR engine
- **Confidence Scoring** - Filters results by accuracy threshold
- **Multiple Formats** - Supports JPEG, PNG, PDF, and more
- **Language Support** - Configurable language detection

## How It Works

```
Image File → Tesseract OCR → Text Extraction → Confidence Check → Result
     ↓              ↓              ↓                ↓              ↓
File Download   Text Analysis   Raw Text      Threshold Filter   Database
```

## Supported Formats

| Format | Extension | Support Level |
|--------|-----------|---------------|
| **JPEG** | `.jpg`, `.jpeg` | ✅ Full |
| **PNG** | `.png` | ✅ Full |
| **PDF** | `.pdf` | ✅ Full |
| **TIFF** | `.tiff`, `.tif` | ✅ Full |
| **BMP** | `.bmp` | ✅ Full |
| **GIF** | `.gif` | ⚠️ Limited |

## Configuration

### Environment Variables
```bash
# OCR languages (comma-separated)
OCR_LANGUAGES=eng,spa,fra

# Minimum confidence threshold (0-100)
OCR_CONFIDENCE_THRESHOLD=60
```

### Language Codes
| Language | Code | Description |
|----------|------|-------------|
| **English** | `eng` | Default, most accurate |
| **Spanish** | `spa` | Spanish text |
| **French** | `fra` | French text |
| **German** | `deu` | German text |
| **Portuguese** | `por` | Portuguese text |

## Usage Examples

### Basic OCR Processing
```python
from src.ocr import ocr_processor

# Process image file
result = await ocr_processor.process_image("/path/to/image.jpg")

print(result['text'])        # Extracted text
print(result['confidence'])  # Confidence score (0-100)
print(result['success'])     # Processing success
```

### Process Image Bytes
```python
# Process image from memory
with open("image.jpg", "rb") as f:
    image_bytes = f.read()

result = await ocr_processor.process_image_bytes(image_bytes)
```

### Telegram Integration
```python
# Process Telegram photo
async def process_telegram_photo(message):
    # Get largest photo size
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    # Download and process
    image_bytes = await file.download_as_bytearray()
    result = await ocr_processor.process_image_bytes(bytes(image_bytes))
    
    return result
```

## Response Format

### Successful Processing
```python
{
    "success": True,
    "text": "PayPal verification required. Click here to verify your account.",
    "confidence": 85.5,
    "language": "eng",
    "processing_time": 2.3
}
```

### Failed Processing
```python
{
    "success": False,
    "text": "",
    "confidence": 0.0,
    "error": "Image too blurry or no text detected",
    "processing_time": 1.2
}
```

## Confidence Thresholds

| Threshold | Use Case | Result Quality |
|-----------|----------|----------------|
| **90+** | High accuracy required | Very reliable |
| **70-89** | Standard processing | Good quality |
| **60-69** | Default setting | Acceptable |
| **50-59** | Low quality images | May have errors |
| **< 50** | Poor quality | Not recommended |

### Adjusting Thresholds
```python
# High accuracy for critical documents
ocr_processor.confidence_threshold = 85

# Lower threshold for noisy images
ocr_processor.confidence_threshold = 45
```

## Performance Optimization

### Image Preprocessing
The OCR processor automatically:
- **Resizes large images** to improve speed
- **Converts formats** to optimal types
- **Enhances contrast** for better recognition
- **Removes noise** from scanned documents

### Processing Times
| Image Size | Processing Time | Memory Usage |
|------------|----------------|--------------|
| **< 1MB** | 1-3 seconds | Low |
| **1-5MB** | 3-8 seconds | Medium |
| **5-10MB** | 8-15 seconds | High |
| **> 10MB** | 15+ seconds | Very High |

## Error Handling

### Common Errors
```python
# Image too large
{
    "success": False,
    "error": "Image file too large (>10MB)"
}

# Unsupported format
{
    "success": False,
    "error": "Unsupported image format"
}

# No text detected
{
    "success": False,
    "error": "No text detected in image"
}

# Low confidence
{
    "success": False,
    "error": "Text confidence below threshold"
}
```

### Error Recovery
```python
try:
    result = await ocr_processor.process_image(image_path)
    if not result['success']:
        # Try with lower threshold
        original_threshold = ocr_processor.confidence_threshold
        ocr_processor.confidence_threshold = 30
        result = await ocr_processor.process_image(image_path)
        ocr_processor.confidence_threshold = original_threshold
except Exception as e:
    logger.error("OCR processing failed", error=str(e))
```

## Integration with Fraud Detection

### Automatic Processing
```python
# OCR result is automatically analyzed for fraud
ocr_result = await ocr_processor.process_image_bytes(image_bytes)

if ocr_result['success']:
    # Text is sent to fraud detector
    fraud_result = await fraud_detector.analyze_message(
        message_text=ocr_result['text'],
        message_id=message_id,
        group_id=group_id,
        bot=bot
    )
```

### Database Storage
```python
# OCR results are stored in database
image_id = await db_manager.save_image({
    "message_id": message_id,
    "file_id": file_id,
    "ocr_text": ocr_result['text'],
    "ocr_confidence": ocr_result['confidence']
})
```

## Troubleshooting

### Poor OCR Results
- ✅ **Increase image resolution** - Higher DPI = better results
- ✅ **Improve image quality** - Better lighting, less blur
- ✅ **Adjust confidence threshold** - Lower for difficult images
- ✅ **Try different languages** - Match image language
- ✅ **Preprocess images** - Enhance contrast, remove noise

### Performance Issues
- ✅ **Reduce image size** - Resize large images
- ✅ **Check memory usage** - Monitor RAM consumption
- ✅ **Optimize batch processing** - Process images sequentially
- ✅ **Review processing times** - Check for bottlenecks

### Installation Problems
- ✅ **Install Tesseract** - `apt-get install tesseract-ocr`
- ✅ **Install language packs** - `apt-get install tesseract-ocr-eng`
- ✅ **Check Python packages** - `pip install pytesseract pillow`
- ✅ **Verify image libraries** - Ensure PIL/Pillow works

### Common Issues
```bash
# Tesseract not found
TesseractNotFoundError: tesseract is not installed

# Language pack missing
TesseractError: Error opening data file

# Image format not supported
PIL.UnidentifiedImageError: cannot identify image file
```

---

**💡 Pro Tip**: For best results, use high-contrast images with clear, readable text. Handwritten text and low-quality scans may require lower confidence thresholds.
