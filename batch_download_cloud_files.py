#!/usr/bin/env python3
"""
Batch download script for pre-caching cloud_file from OSWorld task JSON evaluator configs.

This script scans task JSON files in a directory, extracts cloud_file URLs from evaluator.expected,
and downloads them to the local cache directory following the OSWorld evaluator cache structure.

Cache structure: cache/{task_id}/{dest}

Usage:
    python batch_download_cloud_files.py --input_dir evaluation_examples/examples/gimp_new [--cache_dir cache]
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_download_cloud_files.log', mode='a')
    ]
)
logger = logging.getLogger("batch_download_cloud_files")


def extract_cloud_files_from_task(task_file: str) -> List[Dict[str, str]]:
    """
    Extract all cloud_file URLs from a task JSON file's evaluator.expected config.

    Args:
        task_file: Path to the task JSON file

    Returns:
        List of dicts with 'url', 'dest', and 'task_id' keys
    """
    cloud_files = []

    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            task_data = json.load(f)

        task_id = task_data.get('id', 'unknown')
        evaluator = task_data.get('evaluator', {})
        
        # Handle both single expected config and list of expected configs
        expected_configs = evaluator.get('expected', [])
        if isinstance(expected_configs, dict):
            expected_configs = [expected_configs]
        
        for expected in expected_configs:
            if not expected:
                continue
                
            if expected.get('type') == 'cloud_file':
                url = expected.get('path')  # In cloud_file config, 'path' is the URL
                dest = expected.get('dest')
                
                if url and dest:
                    cloud_files.append({
                        'url': url,
                        'dest': dest,
                        'task_id': task_id,
                        'task_file': task_file
                    })
                    
                # Handle multi-file configs
                if expected.get('multi', False):
                    urls = expected.get('path', [])
                    dests = expected.get('dest', [])
                    if isinstance(urls, list) and isinstance(dests, list):
                        for u, d in zip(urls, dests):
                            if u and d:
                                cloud_files.append({
                                    'url': u,
                                    'dest': d,
                                    'task_id': task_id,
                                    'task_file': task_file,
                                    'source': 'evaluator.expected.multi'
                                })

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {task_file}: {e}")
    except Exception as e:
        logger.error(f"Error processing {task_file}: {e}")

    return cloud_files


def scan_directory_for_cloud_files(input_dir: str, cache_dir: str) -> List[Dict[str, str]]:
    """
    Scan a directory for all task JSON files and extract cloud_file URLs.
    Only returns files that don't already exist in cache.

    Args:
        input_dir: Directory containing task JSON files
        cache_dir: Base cache directory

    Returns:
        List of cloud_file entries that need to be downloaded
    """
    all_cloud_files = []
    seen: Set[str] = set()

    input_path = Path(input_dir)
    json_files = list(input_path.glob('*.json'))

    logger.info(f"Found {len(json_files)} JSON files in {input_dir}")

    for json_file in json_files:
        cloud_files = extract_cloud_files_from_task(str(json_file))

        for cf in cloud_files:
            # Deduplicate by task_id + dest
            key = f"{cf['task_id']}_{cf['dest']}"
            if key in seen:
                continue
            seen.add(key)

            # Check if file already exists in cache
            cache_path = os.path.join(cache_dir, cf['task_id'], cf['dest'])

            if os.path.exists(cache_path):
                logger.info(f"Cloud file already cached: {cache_path}, skipping")
            else:
                all_cloud_files.append(cf)

    logger.info(f"Found {len(all_cloud_files)} cloud files to download")

    return all_cloud_files


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

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

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
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to download {url} caused by {e}. Retrying... ({max_retries - i - 1} attempts left)")
            # Clean up partial download
            if os.path.exists(cache_path):
                os.remove(cache_path)

    logger.error(f"Failed to download {url}. No retries left.")
    return False


def batch_download(input_dir: str, cache_dir: str) -> Tuple[int, int]:
    """
    Main batch download function for cloud files.

    Args:
        input_dir: Directory containing task JSON files
        cache_dir: Directory to store cached files

    Returns:
        Tuple of (successful_count, failed_count)
    """
    # Create base cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)

    # Scan for cloud files
    cloud_files = scan_directory_for_cloud_files(input_dir, cache_dir)

    if not cloud_files:
        logger.info("No cloud files to download or all files already cached.")
        return (0, 0)

    # Download files
    successful = 0
    failed = 0

    logger.info(f"\nStarting batch download of cloud files to cache directory: {cache_dir}")
    logger.info("Files will be organized in task-specific subdirectories (e.g., cache/{task_id}/{dest})")
    logger.info("=" * 80)

    for i, cf in enumerate(cloud_files, 1):
        url = cf['url']
        dest = cf['dest']
        task_id = cf['task_id']

        # Generate cache path: cache/{task_id}/{dest}
        cache_path = os.path.join(cache_dir, task_id, dest)

        logger.info(f"\n[{i}/{len(cloud_files)}] Task: {task_id}")
        logger.info(f"URL: {url}")
        logger.info(f"Dest: {dest}")
        logger.info(f"Cache Path: {cache_path}")

        if download_file(url, cache_path):
            successful += 1
            logger.info("✓ Download successful")
        else:
            failed += 1
            logger.error("✗ Download failed")

        # Small delay between downloads to avoid rate limiting
        if i < len(cloud_files):
            import time
            time.sleep(0.5)

    logger.info("\n" + "=" * 80)
    logger.info("Batch download completed!")
    logger.info(f"Successful: {successful}/{len(cloud_files)}")
    logger.info(f"Failed: {failed}/{len(cloud_files)}")

    return (successful, failed)


def main():
    parser = argparse.ArgumentParser(
        description="Batch download cloud_file from OSWorld task JSON evaluator configs to local cache"
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
