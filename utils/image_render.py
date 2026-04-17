#!/usr/bin/env python3
"""
在图片上渲染半透明红色圆圈，中心带深红色小点
"""

from PIL import Image, ImageDraw
import argparse


def add_red_circle(
    input_path: str,
    output_path: str,
    center: tuple[int, int] | None = None,
    outer_radius: int = 10,
    inner_radius: int = 2,
    outer_color: tuple[int, int, int, int] = (255, 0, 0, 100),  # 半透明红色
    inner_color: tuple[int, int, int, int] = (180, 0, 0, 220),  # 深红色
):
    """
    在图片上绘制半透明红色圆圈和中心深红点
    
    参数:
        input_path: 输入图片路径
        output_path: 输出图片路径
        center: 圆心坐标 (x, y)，默认为图片中心
        outer_radius: 外圈半径
        inner_radius: 中心点半径
        outer_color: 外圈颜色 (R, G, B, A)
        inner_color: 中心点颜色 (R, G, B, A)
    """
    # 打开原图并转换为RGBA模式
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size
    
    # 如果没有指定中心，使用图片中心
    if center is None:
        center = (width // 2, height // 2)
    
    # 创建透明图层用于绘制
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 绘制外圈（半透明红色）
    x, y = center
    draw.ellipse(
        [x - outer_radius, y - outer_radius, x + outer_radius, y + outer_radius],
        fill=outer_color
    )
    
    # 绘制中心点（深红色）
    draw.ellipse(
        [x - inner_radius, y - inner_radius, x + inner_radius, y + inner_radius],
        fill=inner_color
    )
    
    # 合并图层
    result = Image.alpha_composite(img, overlay)
    
    # 保存结果
    result.save(output_path)
    print(f"已保存到: {output_path}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="在图片上添加半透明红色圆圈标记")
    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("-o", "--output", help="输出图片路径", default="output.png")
    parser.add_argument("-x", type=int, help="圆心X坐标（默认为图片中心）")
    parser.add_argument("-y", type=int, help="圆心Y坐标（默认为图片中心）")
    parser.add_argument("-r", "--radius", type=int, default=10, help="外圈半径（默认10）")
    parser.add_argument("-ir", "--inner-radius", type=int, default=1, help="中心点半径（默认1）")
    
    args = parser.parse_args()
    
    center = None
    if args.x is not None and args.y is not None:
        center = (args.x, args.y)
    
    add_red_circle(
        input_path=args.input,
        output_path=args.output,
        center=center,
        outer_radius=args.radius,
        inner_radius=args.inner_radius,
    )


if __name__ == "__main__":
    main()