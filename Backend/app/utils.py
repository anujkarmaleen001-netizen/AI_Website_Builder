import requests
import asyncio
import openai
import glob
import os
import time
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import AsyncOpenAI
import aiofiles

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DALLE_MODEL = os.getenv("DALLE_MODEL", "dall-e-3")

logger.info("=" * 60)
logger.info("OpenAI Configuration:")
logger.info(f"  API Key: {'***SET***' if OPENAI_API_KEY else 'NOT SET'}")
logger.info(f"  Model: {OPENAI_MODEL}")
logger.info(f"  DALL-E Model: {DALLE_MODEL}")
logger.info("=" * 60)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger.info(f"Upload directory: {UPLOAD_DIR}")

# Initialize OpenAI client (used for DALL-E image generation)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
if not openai_client:
    logger.warning("OpenAI client not initialized - API key missing!")


async def download_and_save_image(image_url: str, filepath: str) -> None:
    """
    Download image from DALL-E URL and save to local file path.
    Uses requests library to handle Azure Blob Storage redirects correctly.
    
    Args:
        image_url: URL of the image to download from DALL-E
        filepath: Local file path where image will be saved
    
    Raises:
        HTTPException: If download or save fails
    """
    logger.info(f"Downloading image from: {image_url[:100]}...")
    
    try:
        # Use requests.get() wrapped in executor
        # This handles Azure Blob Storage redirects correctly without breaking signature authentication
        logger.info("Sending GET request to download image...")
        
        def download_image():
            """Synchronous download function to run in executor"""
            img_response = requests.get(image_url, timeout=120)
            img_response.raise_for_status()
            return img_response.content
        
        # Run requests.get() in executor to make it async-compatible
        image_bytes = await asyncio.to_thread(download_image)
        
        logger.info(f"Response status: 200")
        logger.info(f"Image bytes downloaded: {len(image_bytes)} bytes")
        
        # Verify we got actual image data
        if len(image_bytes) == 0:
            logger.error("Downloaded image is empty")
            raise HTTPException(status_code=500, detail="Downloaded image is empty")
        
        # Verify file size (max 10MB)
        size_mb = len(image_bytes) / (1024 * 1024)
        logger.info(f"Image size: {size_mb:.2f} MB")
        if len(image_bytes) > 10 * 1024 * 1024:
            logger.error(f"Image too large: {size_mb:.2f} MB")
            raise HTTPException(
                status_code=400,
                detail="Image file too large (max 10MB)"
            )
        
        # Verify it's actually an image by checking magic bytes
        image_signatures = {
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'\xff\xd8\xff': 'JPEG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
        }
        detected_format = None
        for signature, fmt in image_signatures.items():
            if image_bytes.startswith(signature):
                detected_format = fmt
                break
        
        # Check for WEBP more carefully (RIFF...WEBP)
        if not detected_format and image_bytes[:4] == b'RIFF' and b'WEBP' in image_bytes[:20]:
            detected_format = 'WEBP'
        
        if detected_format:
            logger.info(f"Detected image format: {detected_format}")
        else:
            logger.warning("Could not detect image format from magic bytes, proceeding anyway...")
        
        # Write to file using aiofiles
        logger.info(f"Writing to file: {filepath}")
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(image_bytes)
        
        logger.info("File write completed")
        
        # Verify file was written successfully
        if not os.path.exists(filepath):
            logger.error(f"File not found after write: {filepath}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save image file"
            )
        
        # Verify file size > 0
        file_size = os.path.getsize(filepath)
        logger.info(f"File size: {file_size} bytes")
        if file_size == 0:
            logger.error("File is empty after write")
            raise HTTPException(
                status_code=500,
                detail="Saved image file is empty"
            )
        
        logger.info("✓ Image download and save successful")
    
    except requests.exceptions.HTTPError as e:
        error_text = str(e)
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500
        logger.error(f"HTTP Error: {status_code}")
        logger.error(f"Error: {error_text}")
        raise HTTPException(
            status_code=status_code,
            detail=f"Failed to download image: {error_text}"
        )
    except requests.exceptions.Timeout:
        logger.error("Download timeout after 120 seconds")
        raise HTTPException(status_code=504, detail="Image download timeout. Please try again.")
    except requests.exceptions.RequestException as e:
        error_text = str(e)
        logger.error(f"Request Error: {error_text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download image: {error_text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error downloading image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")


async def call_dalle(section: str, prompt: str, size: str = "1024x1024", quality: str = "standard") -> str:
    """
    Generate image using DALL-E 3, download it, and save to local storage.
    
    Args:
        section: Section name (hero, features, testimonials)
        prompt: Image generation prompt
        size: Image size (1024x1024 or 1792x1024)
        quality: Image quality (standard or hd)
    
    Returns:
        Local file URL path (e.g., "/uploads/hero_1704123456.png")
    
    Raises:
        HTTPException: If generation, download, or storage fails
    """
    logger.info("-" * 60)
    logger.info(f"DALL-E API Call - Image Generation for {section}")
    logger.info(f"Model: {DALLE_MODEL}")
    logger.info(f"Size: {size}")
    logger.info(f"Quality: {quality}")
    logger.info(f"Prompt length: {len(prompt)} chars")
    logger.info(f"Prompt preview: {prompt[:150]}...")
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not configured")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    if not openai_client:
        logger.error("OpenAI client not initialized")
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")
    
    try:
        # Generate image via DALL-E API
        logger.info("Sending request to DALL-E API...")
        response = await openai_client.images.generate(
            model=DALLE_MODEL,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1
        )
        
        logger.info("✓ DALL-E API response received")
        logger.info(f"  Response created: {response.created}")
        logger.info(f"  Images count: {len(response.data)}")
        
        # Extract image URL from response
        image_url = response.data[0].url
        if not image_url:
            logger.error("No image URL in DALL-E response")
            raise HTTPException(status_code=500, detail="No image URL returned from DALL-E API")
        
        # Strip whitespace from URL
        image_url = image_url.strip()
        
        logger.info(f"  Image URL received (length: {len(image_url)})")
        logger.info(f"  URL preview: {image_url[:80]}...")
        
        # Generate filename with timestamp
        timestamp = int(time.time())
        filename = f"{section}_{timestamp}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        logger.info(f"  Target filepath: {filepath}")
        
        # Download and save image
        logger.info("Downloading image from DALL-E URL...")
        await download_and_save_image(image_url, filepath)
        logger.info("✓ Image downloaded and saved")
        
        # Return local URL path (normalize for cross-platform)
        local_url = os.path.join("/uploads", filename).replace("\\", "/")
        
        # Verify file exists before returning
        if not os.path.exists(filepath):
            logger.error(f"Image file not found after save: {filepath}")
            raise HTTPException(status_code=500, detail="Image file not found after save")
        
        file_size = os.path.getsize(filepath)
        logger.info(f"✓ Image saved successfully: {filename} ({file_size} bytes)")
        logger.info(f"  Local URL: {local_url}")
        logger.info("-" * 60)
        
        return local_url
    
    except openai.AuthenticationError as e:
        logger.error(f"DALL-E Authentication Error: {str(e)}")
        logger.error(f"Error details: {e.__dict__}")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid OpenAI API key")
    
    except openai.RateLimitError as e:
        logger.error(f"DALL-E Rate Limit Error: {str(e)}")
        logger.error(f"Error details: {e.__dict__}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    except openai.APITimeoutError as e:
        logger.error(f"DALL-E Timeout Error: {str(e)}")
        logger.error(f"Error details: {e.__dict__}")
        raise HTTPException(status_code=504, detail="Request timeout. Please try again.")
    
    except openai.BadRequestError as e:
        logger.error(f"DALL-E Bad Request Error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__}")
        logger.error(f"Error message: {e.message if hasattr(e, 'message') else 'N/A'}")
        error_code = e.code if hasattr(e, 'code') else 'N/A'
        logger.error(f"Error code: {error_code}")
        
        # Check for billing/quota errors
        error_str = str(e).lower()
        error_detail_str = str(e.__dict__).lower()
        is_billing_error = (
            "billing" in error_str or
            "billing" in error_detail_str or
            "hard limit" in error_str or
            "hard limit" in error_detail_str or
            "quota" in error_str or
            "quota" in error_detail_str or
            error_code == "billing_hard_limit_reached"
        )
        
        if is_billing_error:
            logger.warning("Billing/quota error detected in DALL-E call")
            raise HTTPException(
                status_code=400,
                detail=f"Bad request: Billing hard limit has been reached. Error: {str(e)}"
            )
        
        raise HTTPException(status_code=400, detail=f"Bad request: Error code: {error_code} - {str(e)}")
    
    except openai.APIError as e:
        logger.error(f"DALL-E API Error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__}")
        logger.error(f"Error message: {e.message if hasattr(e, 'message') else 'N/A'}")
        logger.error(f"Error code: {e.code if hasattr(e, 'code') else 'N/A'}")
        logger.error(f"Error param: {e.param if hasattr(e, 'param') else 'N/A'}")
        logger.error(f"Error type (attr): {e.type if hasattr(e, 'type') else 'N/A'}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"DALL-E Unexpected Error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__}")
        logger.error("Full traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating image with DALL-E: {str(e)}")


def find_local_images() -> dict:
    """
    Find the most recent local images from the uploads folder matching the required patterns.
    Returns a dictionary with section names as keys and local file paths as values.
    """
    images = {}
    section_patterns = {
        "hero": "hero_*.png",
        "features": "features_*.png",
        "testimonials": "testimonials_*.png"
    }
    
    for section, pattern in section_patterns.items():
        # Search for files matching the pattern
        search_pattern = os.path.join(UPLOAD_DIR, pattern)
        matching_files = glob.glob(search_pattern)
        
        if matching_files:
            # Sort by modification time (most recent first)
            matching_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            # Get the most recent file
            most_recent = matching_files[0]
            # Convert to relative path for serving
            relative_path = os.path.join("/uploads", os.path.basename(most_recent))
            images[section] = relative_path.replace("\\", "/")  # Normalize path separators
    
    return images
