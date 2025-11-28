#!/usr/bin/env python3
"""
控制台程序 - 处理文件上传、输出格式和下载功能
"""

import argparse
import sys
import os


def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="控制台程序 - 处理文件上传、输出格式和下载功能",
        add_help=False
    )
    
    # 添加参数
    parser.add_argument(
        '--help', 
        action='help',
        default=argparse.SUPPRESS,
        help='显示帮助信息'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        metavar='FILE_PATH',
        help='指定要上传的文件（包括路径）'
    )
    
    parser.add_argument(
        '--otype',
        type=str,
        choices=['video', 'audio'],
        metavar='OUTPUT_TYPE',
        help='输出格式：video 或 audio'
    )
    
    parser.add_argument(
        '--download',
        type=str,
        metavar='DOWNLOAD_PATH',
        help='指定下载文件路径'
    )
    
    # 解析参数
    try:
        args = parser.parse_args()
    except SystemExit:
        # 当用户使用 --help 时，argparse 会调用 sys.exit()
        # 我们捕获这个异常但不做任何处理，让程序正常退出
        return
    
    # 打印所有获取到的参数
    print("获取到的参数：")
    print(f"  --file: {args.file}")
    print(f"  --otype: {args.otype}")
    print(f"  --download: {args.download}")
    
    # 验证文件路径（如果提供了的话）
    if args.file:
        if os.path.exists(args.file):
            print(f"✓ 文件 '{args.file}' 存在")
        else:
            print(f"✗ 文件 '{args.file}' 不存在")
            sys.exit(1)
    
    # 验证下载路径（如果提供了的话）
    if args.download:
        download_dir = os.path.dirname(args.download)
        if download_dir and not os.path.exists(download_dir):
            print(f"✗ 下载目录 '{download_dir}' 不存在")
            sys.exit(1)


if __name__ == "__main__":
    main()
