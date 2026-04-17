#!/usr/bin/env python3
"""
Merge multiple converted_training_data.jsonl files and unified_images directories.

Usage:
    python merge_converted_data.py \
        --input_dirs dir1 dir2 dir3 \
        --output_dir merged_output \
        --output_jsonl merged_training_data.jsonl
"""

import argparse
import json
import os
import shutil
from pathlib import Path

def merge_converted_data(input_dirs, output_dir, output_jsonl):
    """Merge multiple converted data directories."""
    os.makedirs(output_dir, exist_ok=True)
    unified_images_dir = os.path.join(output_dir, "unified_images")
    os.makedirs(unified_images_dir, exist_ok=True)
    
    all_records = []
    copied_images = set()
    unique_task_ids = set()
    total_steps = 0
    
    for input_dir in input_dirs:
        if not os.path.isdir(input_dir):
            print(f"Warning: {input_dir} is not a directory, skipping")
            continue
        
        # Find converted_training_data.jsonl
        jsonl_file = os.path.join(input_dir, "converted_training_data.jsonl")
        if not os.path.exists(jsonl_file):
            print(f"Warning: {jsonl_file} not found, skipping {input_dir}")
            continue
        
        # Find unified_images directory
        images_dir = os.path.join(input_dir, "unified_images")
        if not os.path.exists(images_dir):
            images_dir = None
            print(f"Warning: unified_images not found in {input_dir}")
        
        # Read JSONL records
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    all_records.append(record)
                    # Collect unique task_ids
                    task_id = record.get("task_id")
                    if task_id:
                        unique_task_ids.add(task_id)
                    
                    # Count steps (number of human messages, each represents a step)
                    conversations = record.get("conversations", [])
                    human_messages = sum(1 for conv in conversations if conv.get("from") == "human")
                    total_steps += human_messages
        
        # Copy images
        if images_dir:
            for img_file in os.listdir(images_dir):
                if img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    source = os.path.join(images_dir, img_file)
                    dest = os.path.join(unified_images_dir, img_file)
                    
                    # Skip if already copied (UUID names should be unique, but check anyway)
                    if img_file not in copied_images:
                        shutil.copy2(source, dest)
                        copied_images.add(img_file)
    
    # Write merged JSONL
    output_path = os.path.join(output_dir, output_jsonl)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Print statistics
    avg_steps = total_steps / len(all_records) if all_records else 0
    print(f"Merged {len(all_records)} records to {output_path}")
    print(f"Copied {len(copied_images)} images to {unified_images_dir}")
    print(f"Unique task IDs: {len(unique_task_ids)}")
    print(f"Total steps: {total_steps}")
    print(f"Average steps per task: {avg_steps:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Merge multiple converted training data files")
    parser.add_argument("--input_dirs", nargs="+", required=True, help="Input directories to merge")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    parser.add_argument("--output_jsonl", type=str, default="converted_training_data.jsonl", 
                       help="Output JSONL filename")
    
    args = parser.parse_args()
    merge_converted_data(args.input_dirs, args.output_dir, args.output_jsonl)


if __name__ == "__main__":
    main()
