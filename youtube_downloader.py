import argparse
import sys
import os
import subprocess
import yt_dlp


def download_video(url, output_dir, quality='best', audio_only=False, merge=True):
    output_path = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
    }
    
    if audio_only:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        if merge:
            ydl_opts['format'] = f'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'
        else:
            ydl_opts['format'] = f'{quality}[ext=mp4]/best[ext=mp4]/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'unknown')
            print(f"\n下载完成: {video_title}")
            return True
    except yt_dlp.DownloadError as e:
        print(f"下载错误: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return False


def list_formats(url):
    ydl_opts = {
        'listformats': True,
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"获取格式信息失败: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='YouTube 视频下载工具')
    parser.add_argument('url', help='YouTube 视频 URL')
    parser.add_argument('-o', '--output', default='.', help='输出目录 (默认: 当前目录)')
    parser.add_argument('-q', '--quality', default='best', help='视频质量 (best, 720p, 1080p 等)')
    parser.add_argument('-a', '--audio-only', action='store_true', help='仅下载音频')
    parser.add_argument('-l', '--list-formats', action='store_true', help='列出可用格式')
    parser.add_argument('-n', '--no-merge', action='store_true', help='不合并音视频 (可能只有视频或音频)')
    
    args = parser.parse_args()
    
    output_dir = os.path.abspath(args.output)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if args.list_formats:
        list_formats(args.url)
        return
    
    print(f"正在下载: {args.url}")
    print(f"输出目录: {output_dir}")
    
    success = download_video(
        args.url,
        output_dir,
        quality=args.quality,
        audio_only=args.audio_only,
        merge=not args.no_merge
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
