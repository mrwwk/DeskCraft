#!/usr/bin/env python3
"""
Convert training data from JSONL format to template.json format.
Merges all steps from each task into a single conversation.

Usage:
    python convert_training_data_to_template.py \
        --results_base_dir ./results \
        --output_dir ./converted_data \
        --model qwen3-vl \
        --unified_images_dir ./unified_images
"""

import argparse
import json
import os
import uuid
import shutil
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_task_success(example_path: str) -> bool:
    """Check if task is successful (result.txt != 0)."""
    result_file = os.path.join(example_path, "result.txt")
    if not os.path.exists(result_file):
        return False
    try:
        with open(result_file, "r") as f:
            result = float(f.read().strip())
            return result != 0.0
    except:
        return False


def check_terminate_success_in_data(training_data_file: str) -> bool:
    """Check if training data contains terminate action with success status."""
    if not os.path.exists(training_data_file):
        return False
    try:
        with open(training_data_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    response = record.get("response", "")
                    # 检查是否包含 {"action": "terminate", "status": "success"} 的JSON格式
                    # 只要response中同时包含这两个字符串就认为匹配
                    if '"action": "terminate"' in response and '"status": "success"' in response:
                        return True
    except:
        return False
    return False


def copy_and_rename_image(source_path: str, unified_dir: str, image_mapping: Dict[str, str], dry_run: bool = False) -> str:
    """Copy image to unified directory with UUID name, deduplicate."""
    normalized = os.path.abspath(source_path)
    if normalized in image_mapping:
        return image_mapping[normalized]
    
    if not os.path.exists(source_path):
        return None
    
    ext = os.path.splitext(source_path)[1] or ".png"
    uuid_name = f"{uuid.uuid4()}{ext}"
    dest_path = os.path.join(unified_dir, uuid_name)
    
    if dry_run:
        # Dry-run模式：只记录映射，不实际复制文件
        image_mapping[normalized] = uuid_name
        return uuid_name
    
    try:
        shutil.copy2(source_path, dest_path)
        image_mapping[normalized] = uuid_name
        return uuid_name
    except Exception as e:
        logger.error(f"Failed to copy {source_path}: {e}")
        return None


def extract_images_from_messages(messages: List[Dict], images_base_dir: str, 
                                  unified_dir: str, image_mapping: Dict[str, str], dry_run: bool = False) -> List[str]:
    """Extract and copy images from messages, return UUID filenames."""
    image_paths = []
    for msg in messages:
        for item in msg.get("content", []):
            if item.get("type") == "image_url":
                img_path = item.get("image_path")
                if img_path and images_base_dir:
                    source = os.path.join(images_base_dir, img_path)
                    if unified_dir:
                        new_path = copy_and_rename_image(source, unified_dir, image_mapping, dry_run)
                        if new_path:
                            image_paths.append(new_path)
                    else:
                        image_paths.append(os.path.basename(img_path))
    return image_paths


def extract_action_and_code(response: str) -> tuple:
    """Extract action and code from response."""
    action = None
    code = None
    
    for line in response.split("\n"):
        if line.strip().startswith("Action:"):
            action = line.split("Action:", 1)[1].strip()
            break
    
    code_start = response.find("<tool_call>")
    if code_start != -1:
        code_end = response.find("</tool_call>", code_start)
        if code_end != -1:
            code = response[code_start:code_end + len("</tool_call>")]
    
    return action, code


def convert_messages_to_conversations(messages: List[Dict], response: str) -> List[Dict]:
    """Convert messages to conversation format."""
    conversations = []
    
    for msg in messages:
        role = msg.get("role", "")
        if role == "system":
            continue
        
        content_items = msg.get("content", [])
        if role == "user":
            value_parts = []
            for item in content_items:
                if item.get("type") == "image_url":
                    value_parts.append("<image>")
                elif item.get("type") == "text":
                    text = item.get("text", "").strip()
                    if text:
                        value_parts.append(text)
            if value_parts:
                conversations.append({"from": "human", "value": "\n".join(value_parts)})
        
        elif role == "assistant":
            text_parts = [item.get("text", "") for item in content_items if item.get("type") == "text"]
            if text_parts:
                conversations.append({"from": "gpt", "value": "\n".join(text_parts)})
    
    # Add current response
    if response:
        action, code = extract_action_and_code(response)
        conv = {"from": "gpt", "value": response}
        if action:
            conv["action"] = action
        if code:
            conv["code"] = code
        conversations.append(conv)
    
    return conversations


def merge_task_records(records: List[Dict], task_id: str, source: str, split: str,
                       images_base_dir: str, unified_dir: str, image_mapping: Dict[str, str], dry_run: bool = False) -> Dict[str, Any]:
    """Merge all step records from a task into a single conversation."""
    if not records:
        return None
    
    sorted_records = sorted(records, key=lambda x: x.get("step", 0))
    all_images = []
    all_conversations = []
    seen_images = set()
    
    for idx, record in enumerate(sorted_records):
        messages = record.get("input", {}).get("messages", [])
        response = record.get("response", "")
        
        # Extract images
        step_images = extract_images_from_messages(messages, images_base_dir, unified_dir, image_mapping, dry_run)
        for img in step_images:
            if img not in seen_images:
                all_images.append(img)
                seen_images.add(img)
        
        # Extract conversations
        if idx == 0:
            # First step: include all conversations
            step_convs = convert_messages_to_conversations(messages, response)
            all_conversations.extend(step_convs)
        else:
            # Subsequent steps: only new user message and response
            last_user = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user = msg
                    break
            
            if last_user:
                value_parts = []
                for item in last_user.get("content", []):
                    if item.get("type") == "image_url":
                        value_parts.append("<image>")
                    elif item.get("type") == "text":
                        text = item.get("text", "").strip()
                        if text:
                            value_parts.append(text)
                if value_parts:
                    all_conversations.append({"from": "human", "value": "\n".join(value_parts)})
            
            if response:
                action, code = extract_action_and_code(response)
                conv = {"from": "gpt", "value": response}
                if action:
                    conv["action"] = action
                if code:
                    conv["code"] = code
                all_conversations.append(conv)
    
    return {
        "id": f"agentnet_sft_{task_id}",
        "task_id": task_id,
        "source": source,
        "task_type": "gui_agent_planning",
        "split": split,
        "images": all_images,
        "conversations": all_conversations
    }


def convert_tasks(results_base_dir: str, output_dir: str, action_space: str, 
                  observation_type: str, model: str, source: str, split: str,
                  unified_images_dir: str = None, check_success: bool = True, dry_run: bool = False):
    """Convert training data from multiple tasks."""
    base_path = os.path.join(results_base_dir, action_space, observation_type, model)
    if not os.path.exists(base_path):
        logger.error(f"Base path not found: {base_path}")
        return
    
    if dry_run:
        logger.info("="*80)
        logger.info("DRY-RUN 模式：只进行统计，不实际写入文件或复制图片")
        logger.info("="*80)
    else:
        os.makedirs(output_dir, exist_ok=True)
        if unified_images_dir:
            os.makedirs(unified_images_dir, exist_ok=True)
            logger.info(f"Unified images directory: {unified_images_dir}")
    
    all_records = []
    image_mapping = {}
    skipped = 0
    processed = 0
    terminate_success_but_failed = []  # 存储有terminate success但result.txt为0的任务ID
    
    for domain in os.listdir(base_path):
        domain_path = os.path.join(base_path, domain)
        if not os.path.isdir(domain_path):
            continue
        
        for example_id in os.listdir(domain_path):
            example_path = os.path.join(domain_path, example_id)
            if not os.path.isdir(example_path):
                continue
            
            training_data_file = os.path.join(example_path, "training_data", "training_data.jsonl")
            
            # 检查是否有terminate success但result.txt为0的情况
            if check_terminate_success_in_data(training_data_file) and not check_task_success(example_path):
                task_full_id = f"{domain}/{example_id}"
                terminate_success_but_failed.append(task_full_id)
            
            if check_success and not check_task_success(example_path):
                skipped += 1
                continue
            
            images_base_dir = os.path.join(example_path, "training_data", "screenshots")
            
            if not os.path.exists(training_data_file):
                continue
            
            # Read all records for this task
            task_records = []
            try:
                with open(training_data_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            task_records.append(json.loads(line))
            except Exception as e:
                logger.warning(f"Error reading {domain}/{example_id}: {e}")
                continue
            
            if not task_records:
                continue
            
            # Merge into single conversation
            try:
                record = merge_task_records(
                    task_records, example_id, source, split,
                    images_base_dir, unified_images_dir, image_mapping, dry_run
                )
                if record:
                    all_records.append(record)
                    processed += 1
                    logger.info(f"Processed: {domain}/{example_id}")
            except Exception as e:
                logger.warning(f"Error processing {domain}/{example_id}: {e}")
                continue
    
    # Write output (skip in dry-run mode)
    if not dry_run:
        output_file = os.path.join(output_dir, "converted_training_data.jsonl")
        with open(output_file, "w", encoding="utf-8") as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info(f"Converted {len(all_records)} tasks to {output_file}")
    else:
        logger.info(f"DRY-RUN: 将转换 {len(all_records)} 个任务（未实际写入文件）")
    if check_success and skipped > 0:
        logger.info(f"Skipped {skipped} failed tasks")
    
    # 单独打印有terminate success但result.txt为0的任务ID
    if terminate_success_but_failed:
        logger.info("\n" + "="*80)
        logger.info("以下任务在训练数据中显示 terminate success，但 result.txt 为 0（评估认为未完成）：")
        logger.info("="*80)
        for task_id in terminate_success_but_failed:
            logger.info(f"  - {task_id}")
        logger.info(f"\n总共 {len(terminate_success_but_failed)} 个任务需要检查")
        logger.info("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Convert training data to template format")
    parser.add_argument("--results_base_dir", type=str, required=True, help="Base directory containing results")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    parser.add_argument("--model", type=str, required=True, help="Model name")
    parser.add_argument("--action_space", type=str, default="pyautogui", help="Action space")
    parser.add_argument("--observation_type", type=str, default="screenshot", help="Observation type")
    parser.add_argument("--source", type=str, default="osworld", help="Data source")
    parser.add_argument("--split", type=str, default="train", choices=["train", "val", "test"], help="Split")
    parser.add_argument("--unified_images_dir", type=str, default=None, help="Unified images directory (UUID renamed)")
    parser.add_argument("--include_failed", action="store_true", help="Include failed tasks")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode: only statistics, no file writing or image copying")
    
    args = parser.parse_args()
    
    convert_tasks(
        results_base_dir=args.results_base_dir,
        output_dir=args.output_dir,
        action_space=args.action_space,
        observation_type=args.observation_type,
        model=args.model,
        source=args.source,
        split=args.split,
        unified_images_dir=args.unified_images_dir,
        check_success=not args.include_failed,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
