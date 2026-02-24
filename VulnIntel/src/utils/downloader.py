"""File download utilities with retry logic."""

import gzip
import shutil
import time
import zipfile
from pathlib import Path
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import DOWNLOAD_CONFIG
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_session() -> requests.Session:
    """
    Create a requests session with retry logic.
    
    Returns:
        Configured requests session
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=DOWNLOAD_CONFIG["max_retries"],
        backoff_factor=DOWNLOAD_CONFIG["retry_delay"],
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({"User-Agent": DOWNLOAD_CONFIG["user_agent"]})
    
    return session


def download_file(
    url: str,
    output_path: Path,
    decompress: bool = True,
    timeout: Optional[int] = None,
) -> Path:
    """
    Download a file with retry logic and optional decompression.
    
    Args:
        url: URL to download from
        output_path: Path to save the file
        decompress: Whether to decompress gzip/zip files
        timeout: Request timeout in seconds (defaults to config)
        
    Returns:
        Path to the downloaded (and possibly decompressed) file
        
    Raises:
        requests.RequestException: If download fails after retries
    """
    if timeout is None:
        timeout = DOWNLOAD_CONFIG["timeout"]
    
    logger.info(f"Downloading: {url}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    session = create_session()
    
    try:
        response = session.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Download to temporary file first
        temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CONFIG["chunk_size"]):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Progress: {progress:.1f}%")
        
        # Move to final location
        shutil.move(str(temp_path), str(output_path))
        logger.info(f"Downloaded: {output_path} ({downloaded:,} bytes)")
        
        # Decompress if needed
        if decompress:
            if output_path.suffix == ".gz":
                return decompress_gzip(output_path)
            elif output_path.suffix == ".zip":
                return decompress_zip(output_path)
        
        return output_path
        
    except requests.RequestException as e:
        logger.error(f"Download failed: {url} - {e}")
        raise


def decompress_gzip(gz_path: Path) -> Path:
    """
    Decompress a gzip file.
    
    Args:
        gz_path: Path to gzip file
        
    Returns:
        Path to decompressed file
    """
    output_path = gz_path.with_suffix("")
    
    logger.info(f"Decompressing: {gz_path}")
    
    with gzip.open(gz_path, "rb") as f_in:
        with open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    logger.info(f"Decompressed: {output_path}")
    
    # Remove compressed file
    gz_path.unlink()
    
    return output_path


def decompress_zip(zip_path: Path) -> Path:
    """
    Decompress a zip file (extracts first file).
    
    Args:
        zip_path: Path to zip file
        
    Returns:
        Path to extracted file
    """
    output_dir = zip_path.parent
    
    logger.info(f"Extracting: {zip_path}")
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Get first file in archive
        file_list = zip_ref.namelist()
        if not file_list:
            raise ValueError(f"Empty zip file: {zip_path}")
        
        first_file = file_list[0]
        zip_ref.extract(first_file, output_dir)
        
        output_path = output_dir / first_file
        logger.info(f"Extracted: {output_path}")
    
    # Remove zip file
    zip_path.unlink()
    
    return output_path


def download_with_cache(
    url: str,
    cache_path: Path,
    max_age_seconds: Optional[int] = None,
) -> Path:
    """
    Download a file with caching support.
    
    Args:
        url: URL to download from
        cache_path: Path to cache file
        max_age_seconds: Maximum age of cached file (None = always use cache)
        
    Returns:
        Path to cached file
    """
    # Check if cached file exists and is fresh
    if cache_path.exists():
        if max_age_seconds is None:
            logger.info(f"Using cached file: {cache_path}")
            return cache_path
        
        age = time.time() - cache_path.stat().st_mtime
        if age < max_age_seconds:
            logger.info(f"Using cached file: {cache_path} (age: {age:.0f}s)")
            return cache_path
        else:
            logger.info(f"Cached file expired (age: {age:.0f}s > {max_age_seconds}s)")
    
    # Download fresh copy
    return download_file(url, cache_path)
