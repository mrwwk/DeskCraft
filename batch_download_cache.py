#!/usr/bin/env python3
"""
Batch download script for pre-caching files from OSWorld task JSON files.

This script scans task JSON files in a directory, extracts download URLs,
and downloads them to the local cache directory following the same naming
convention as the OSWorld setup controller.

Usage:
    python batch_download_cache.py --input_dir evaluation_examples/examples/gimp_new [--cache_dir cache]
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Set, Tuple

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_download.log', mode='a')
    ]
)
logger = logging.getLogger("batch_download")


def generate_cache_filename(url: str, path: str) -> str:
    """
    Generate cache filename following the same convention as setup.py
    
    Args:
        url: The download URL
        path: The destination path on VM
        
    Returns:
        Cache filename: {uuid5}_{basename}
    """
    url_uuid = uuid.uuid5(uuid.NAMESPACE_URL, url)
    basename = os.path.basename(path)
    return f"{url_uuid}_{basename}"


def get_cache_path(url: str, path: str, cache_dir: str) -> str:
    """
    Get the full cache path for a file.
    
    Args:
        url: The download URL
        path: The destination path on VM
        cache_dir: The cache directory
        
    Returns:
        Full path to the cache file
    """
    cache_filename = generate_cache_filename(url, path)
    return os.path.join(cache_dir, cache_filename)


def extract_download_urls_from_task(task_file: str) -> List[Dict[str, str]]:
    """
    Extract all download URLs from a task JSON file.
    
    Args:
        task_file: Path to the task JSON file
        
    Returns:
        List of dicts with 'url', 'path', and 'task_file' keys
    """
    downloads = []
    
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
        
        config = task_data.get('config', [])
        
        for step in config:
            if step.get('type') == 'download':
                files = step.get('parameters', {}).get('files', [])
                for file_info in files:
                    if 'url' in file_info and 'path' in file_info:
                        downloads.append({
                            'url': file_info['url'],
                            'path': file_info['path'],
                            'task_file': task_file,
                            'task_id': task_data.get('id', 'unknown')
                        })
        
        # Also check evaluator for expected/result files that might need downloading
        evaluator = task_data.get('evaluator', {})
        expected = evaluator.get('expected', {})
        if expected.get('type') == 'cloud_file' and 'url' in expected:
            # Note: cloud_file type uses URL but doesn't specify VM path
            # We'll skip these unless they have a 'path' field
            if 'path' in expected:
                downloads.append({
                    'url': expected['url'],
                    'path': expected['path'],
                    'task_file': task_file,
                    'task_id': task_data.get('id', 'unknown'),
                    'source': 'evaluator.expected'
                })
                
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {task_file}: {e}")
    except Exception as e:
        logger.error(f"Error processing {task_file}: {e}")
    
    return downloads


def scan_directory_for_downloads(input_dir: str, cache_dir: str) -> List[Dict[str, str]]:
    """
    Scan a directory for all task JSON files and extract download URLs.
    Downloads are organized by task_id subdirectory to match OSWorld's cache structure.

    Args:
        input_dir: Directory containing task JSON files
        cache_dir: Base cache directory (used to check existing files)

    Returns:
        List of unique download entries (not yet downloaded)
    """
    all_downloads = []
    seen_urls: Set[str] = set()

    input_path = Path(input_dir)
    json_files = list(input_path.glob('*.json'))

    logger.info(f"Found {len(json_files)} JSON files in {input_dir}")

    for json_file in json_files:
        downloads = extract_download_urls_from_task(str(json_file))

        for download in downloads:
            # Deduplicate by URL+task_id combination
            key = f"{download['url']}_{download['task_id']}"
            if key not in seen_urls:
                seen_urls.add(key)
                
                # Check if file already exists in task-specific cache directory
                task_cache_dir = os.path.join(cache_dir, download['task_id'])
                cache_filename = generate_cache_filename(download['url'], download['path'])
                cache_path = os.path.join(task_cache_dir, cache_filename)
                
                if os.path.exists(cache_path):
                    logger.info(f"Cache file already exists: {cache_path}, skipping")
                else:
                    all_downloads.append(download)

    logger.info(f"Found {len(all_downloads)} unique download URLs to process")

    return all_downloads


def download_file(url: str, cache_path: str, max_retries: int = 3) -> bool:
    """
    Download a file from URL to cache path.
    
    Args:
        url: The download URL
        cache_path: The destination path
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if download succeeded, False otherwise
    """
    if os.path.exists(cache_path):
        logger.info(f"Cache file already exists: {cache_path}")
        return True
    
    max_retries = 3
    downloaded = False
    e = None
    
    for i in range(max_retries):
        try:
            logger.info(f"Download attempt {i+1}/{max_retries} for {url}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size > 0:
                logger.info(f"File size: {total_size / (1024*1024):.2f} MB")
            
            downloaded_size = 0
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0 and downloaded_size % (1024*1024) == 0:
                            progress = (downloaded_size / total_size) * 100
                            logger.info(f"Download progress: {progress:.1f}%")
            
            logger.info(f"File downloaded successfully to {cache_path} ({downloaded_size / (1024*1024):.2f} MB)")
            downloaded = True
            break
            
        except requests.RequestException as e:
            logger.error(f"Failed to download {url} caused by {e}. Retrying... ({max_retries - i - 1} attempts left)")
            # Clean up partial download
            if os.path.exists(cache_path):
                os.remove(cache_path)
    
    if not downloaded:
        logger.error(f"Failed to download {url}. No retries left.")
        return False
    
    return True


def batch_download(input_dir: str, cache_dir: str, max_concurrent: int = 5) -> Tuple[int, int]:
    """
    Main batch download function.
    Files are organized in task-specific subdirectories to match OSWorld's cache structure.

    Args:
        input_dir: Directory containing task JSON files
        cache_dir: Directory to store cached files (base directory, task subdirs will be created)
        max_concurrent: Maximum number of concurrent downloads (not used in current sequential implementation)

    Returns:
        Tuple of (successful_count, failed_count)
    """
    # Create base cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)

    # Scan for downloads (this will check for existing files in task subdirs)
    downloads = scan_directory_for_downloads(input_dir, cache_dir)

    if not downloads:
        logger.info("No downloads found or all files already cached.")
        return (0, 0)

    # Download files
    successful = 0
    failed = 0

    logger.info(f"\nStarting batch download to cache directory: {cache_dir}")
    logger.info("Files will be organized in task-specific subdirectories (e.g., cache/{task_id}/)")
    logger.info("=" * 80)

    for i, download in enumerate(downloads, 1):
        url = download['url']
        path = download['path']
        task_id = download.get('task_id', 'unknown')

        # Create task-specific cache directory
        task_cache_dir = os.path.join(cache_dir, task_id)
        os.makedirs(task_cache_dir, exist_ok=True)
        
        # Generate cache path in task-specific directory
        cache_filename = generate_cache_filename(url, path)
        cache_path = os.path.join(task_cache_dir, cache_filename)

        logger.info(f"\n[{i}/{len(downloads)}] Task: {task_id}")
        logger.info(f"URL: {url}")
        logger.info(f"VM Path: {path}")
        logger.info(f"Cache Path: {cache_path}")

        if download_file(url, cache_path):
            successful += 1
            logger.info("✓ Download successful")
        else:
            failed += 1
            logger.error("✗ Download failed")

        # Small delay between downloads to avoid rate limiting
        if i < len(downloads):
            import time
            time.sleep(0.5)

    logger.info("\n" + "=" * 80)
    logger.info("Batch download completed!")
    logger.info(f"Successful: {successful}/{len(downloads)}")
    logger.info(f"Failed: {failed}/{len(downloads)}")

    return (successful, failed)


def main():
    parser = argparse.ArgumentParser(
        description="Batch download files from OSWorld task JSON files to local cache"
    )
    
    parser.add_argument(
        "--input_dir",
        type=str,
        default="evaluation_examples/examples/gimp_new",
        help="Directory containing task JSON files"
    )
    
    parser.add_argument(
        "--cache_dir",
        type=str,
        default="cache",
        help="Directory to store cached files (default: cache)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input directory
    if not os.path.isdir(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        sys.exit(1)
    
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Cache directory: {args.cache_dir}")
    
    # Run batch download
    successful, failed = batch_download(args.input_dir, args.cache_dir)
    
    # Exit with error code if any downloads failed
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
