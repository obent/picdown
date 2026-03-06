import os
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time
import random
import string
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class ImageDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("图片下载与WebP转换工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 变量
        self.is_processing = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入信息", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        input_frame.rowconfigure(0, weight=1)
        
        # 网页URL（改为多行文本框）
        ttk.Label(input_frame, text="网页URL:").grid(row=0, column=0, sticky=(tk.W, tk.N), pady=5)
        url_frame = ttk.Frame(input_frame)
        url_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=(5, 0))
        url_frame.columnconfigure(0, weight=1)
        url_frame.rowconfigure(0, weight=1)
        
        self.url_text = scrolledtext.ScrolledText(url_frame, width=50, height=6, wrap=tk.WORD)
        self.url_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.parse_button = ttk.Button(url_frame, text="批量解析", command=self.parse_urls, width=10)
        self.parse_button.grid(row=0, column=1, sticky=(tk.N))
        
        ttk.Label(input_frame, text="(每行一个网址，点击批量解析后自动处理)", font=("", 8)).grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        # URL前缀（新增）
        ttk.Label(input_frame, text="URL前缀:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.base_url_entry = ttk.Entry(input_frame, width=40)
        self.base_url_entry.insert(0, "https://cfcdn-asia.coseroom.com/wifes/")
        self.base_url_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        ttk.Label(input_frame, text="(生成txt文件时的URL前缀)", font=("", 8)).grid(row=3, column=1, sticky=tk.W, padx=(5, 0))
        
        # 线程数设置（新增）
        thread_frame = ttk.Frame(input_frame)
        thread_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(thread_frame, text="下载线程数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.download_threads = ttk.Spinbox(thread_frame, from_=1, to=20, width=10)
        self.download_threads.set(5)
        self.download_threads.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(thread_frame, text="转换线程数:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.convert_threads = ttk.Spinbox(thread_frame, from_=1, to=20, width=10)
        self.convert_threads.set(4)
        self.convert_threads.grid(row=0, column=3)
        
        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="10")
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(3, weight=1)
        
        # 总体进度
        ttk.Label(progress_frame, text="总体进度:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.overall_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.overall_progress.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        self.overall_label = ttk.Label(progress_frame, text="0/0")
        self.overall_label.grid(row=0, column=2, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # 下载进度
        ttk.Label(progress_frame, text="下载进度:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.download_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.download_progress.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        self.download_label = ttk.Label(progress_frame, text="0/0")
        self.download_label.grid(row=1, column=2, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # 转换进度
        ttk.Label(progress_frame, text="转换进度:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.convert_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.convert_progress.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        self.convert_label = ttk.Label(progress_frame, text="0/0")
        self.convert_label.grid(row=2, column=2, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        progress_frame.columnconfigure(1, weight=1)
        
        # 日志区域
        ttk.Label(progress_frame, text="处理日志:").grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(progress_frame, width=60, height=15, wrap=tk.WORD, state='disabled')
        self.log_text.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
    
    def log(self, message):
        """添加日志"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def update_overall_progress(self, current, total):
        """更新总体进度"""
        self.overall_progress['maximum'] = total
        self.overall_progress['value'] = current
        self.overall_label.config(text=f"{current}/{total}")
    
    def update_download_progress(self, current, total):
        """更新下载进度"""
        self.download_progress['maximum'] = total
        self.download_progress['value'] = current
        self.download_label.config(text=f"{current}/{total}")
    
    def update_convert_progress(self, current, total):
        """更新转换进度"""
        self.convert_progress['maximum'] = total
        self.convert_progress['value'] = current
        self.convert_label.config(text=f"{current}/{total}")
    
    def generate_random_filename(self, length=12):
        """生成随机文件名"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def get_thread_counts(self):
        """获取线程数设置"""
        try:
            download_threads = int(self.download_threads.get())
            convert_threads = int(self.convert_threads.get())
            # 限制范围
            download_threads = max(1, min(20, download_threads))
            convert_threads = max(1, min(20, convert_threads))
            return download_threads, convert_threads
        except:
            return 5, 4  # 默认值
    
    def parse_images_from_url(self, url):
        """从网页解析图片链接和标题"""
        try:
            # 构建完整URL
            if not url.endswith('?page=all'):
                full_url = url.rstrip('/') + '?page=all'
            else:
                full_url = url
            
            self.log(f"正在请求: {full_url}")
            
            # 模拟浏览器请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(full_url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            self.log(f"✓ 请求成功，状态码: {response.status_code}")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取标题
            title = ""
            title_tag = soup.find('h1', class_='focusbox-title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                self.log(f"✓ 找到标题: {title}")
            else:
                self.log("⚠ 未找到 h1.focusbox-title 标签")
            
            # 查找所有图片
            img_tags = soup.find_all('img')
            all_tags_with_src = soup.find_all(attrs={'src': True})
            all_tags_with_data_src = soup.find_all(attrs={'data-src': True})
            all_tags_with_data_original = soup.find_all(attrs={'data-original': True})
            
            self.log(f"找到 {len(img_tags)} 个 <img> 标签")
            
            # 收集所有可能的图片URL
            potential_urls = set()
            
            for img in img_tags:
                for attr in ['src', 'data-src', 'data-original', 'data-lazy-src']:
                    if img.get(attr):
                        potential_urls.add(img[attr])
            
            for tag in all_tags_with_src + all_tags_with_data_src + all_tags_with_data_original:
                for attr in ['src', 'data-src', 'data-original']:
                    if tag.get(attr):
                        url_value = tag[attr]
                        if any(ext in url_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                            potential_urls.add(url_value)
            
            self.log(f"收集到 {len(potential_urls)} 个潜在图片URL")
            
            # 筛选符合条件的图片（前10位为数字）
            pattern = re.compile(r'^\d{10}')
            matched_images = []
            
            for img_url in potential_urls:
                full_img_url = urljoin(full_url, img_url)
                parsed = urlparse(full_img_url)
                filename = parsed.path.split('/')[-1]
                
                if pattern.match(filename):
                    matched_images.append(full_img_url)
                    self.log(f"✓ 匹配: {filename}")
            
            return title, matched_images
        
        except Exception as e:
            self.log(f"✗ 解析失败: {str(e)}")
            return "", []
    
    def parse_urls(self):
        """批量解析URL按钮回调"""
        urls_input = self.url_text.get("1.0", tk.END).strip()
        urls = [line.strip() for line in urls_input.split('\n') if line.strip()]
        
        if not urls:
            messagebox.showerror("错误", "请输入至少一个网页URL")
            return
        
        # 禁用按钮
        self.parse_button.config(state='disabled', text='处理中...')
        
        # 清空日志
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        # 重置进度条
        self.update_overall_progress(0, len(urls))
        self.update_download_progress(0, 100)
        self.update_convert_progress(0, 100)
        
        def batch_process_thread():
            try:
                self.root.after(0, self.log, f"开始批量处理 {len(urls)} 个网址")
                self.root.after(0, self.log, "=" * 60)
                
                completed = 0
                
                for idx, url in enumerate(urls, 1):
                    # 添加协议
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    
                    self.root.after(0, self.log, f"\n[{idx}/{len(urls)}] 处理: {url}")
                    self.root.after(0, self.log, "-" * 60)
                    
                    try:
                        # 解析网页
                        title, images = self.parse_images_from_url(url)
                        
                        if not title:
                            self.root.after(0, self.log, f"⚠ 未找到标题，跳过此网址")
                            continue
                        
                        if not images:
                            self.root.after(0, self.log, f"⚠ 未找到符合条件的图片，跳过此网址")
                            continue
                        
                        # 处理图片
                        self.process_single_task(title, images)
                        
                        completed += 1
                        self.root.after(0, self.update_overall_progress, completed, len(urls))
                        
                    except Exception as e:
                        self.root.after(0, self.log, f"✗ 处理失败: {str(e)}")
                
                self.root.after(0, self.log, f"\n" + "=" * 60)
                self.root.after(0, self.log, f"批量处理完成! 成功: {completed}/{len(urls)}")
                self.root.after(0, self.log, "=" * 60)
                self.root.after(0, messagebox.showinfo, "完成", f"批量处理完成!\n成功: {completed}/{len(urls)}")
                
            except Exception as e:
                self.root.after(0, self.log, f"\n✗ 错误: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"批量处理失败:\n{str(e)}")
            finally:
                self.root.after(0, lambda: self.parse_button.config(state='normal', text='批量解析'))
        
        thread = threading.Thread(target=batch_process_thread, daemon=True)
        thread.start()
    
    def process_single_task(self, folder_name, links):
        """处理单个任务（下载和转换）"""
        try:
            # 获取线程数设置
            download_threads, convert_threads = self.get_thread_counts()
            
            # 创建文件夹
            target_folder = Path(folder_name)
            target_folder.mkdir(exist_ok=True)
            webp_folder = target_folder / "webp"
            webp_folder.mkdir(exist_ok=True)
            
            self.root.after(0, self.log, f"目标文件夹: {folder_name}")
            self.root.after(0, self.log, f"图片数量: {len(links)}")
            self.root.after(0, self.log, f"下载线程: {download_threads}, 转换线程: {convert_threads}")
            
            # 准备下载
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            download_tasks = []
            used_names = set()
            
            for url in links:
                ext = os.path.splitext(url.split('?')[0])[-1] or '.jpg'
                while True:
                    random_name = self.generate_random_filename(12)
                    if random_name not in used_names:
                        used_names.add(random_name)
                        break
                filename = f"{random_name}{ext}"
                save_path = target_folder / filename
                download_tasks.append((url, save_path, headers))
            
            # 多线程下载
            self.root.after(0, self.log, "开始下载...")
            self.root.after(0, self.update_download_progress, 0, len(links))
            
            downloaded_files = []
            download_count = [0]
            
            def download_with_progress(task):
                url, path, hdrs = task
                result = self.download_image(url, path, hdrs)
                download_count[0] += 1
                self.root.after(0, self.update_download_progress, download_count[0], len(links))
                if result:
                    return path
                return None
            
            with ThreadPoolExecutor(max_workers=download_threads) as executor:
                futures = [executor.submit(download_with_progress, task) for task in download_tasks]
                for future in futures:
                    result = future.result()
                    if result:
                        downloaded_files.append(result)
            
            self.root.after(0, self.log, f"下载完成: {len(downloaded_files)}/{len(links)}")
            
            if not downloaded_files:
                self.root.after(0, self.log, "没有成功下载的图片")
                return
            
            # 转换为webp
            self.root.after(0, self.log, "开始转换...")
            self.root.after(0, self.update_convert_progress, 0, len(downloaded_files))
            
            webp_files = []
            convert_count = [0]
            
            def convert_with_progress(img_path):
                output_name = img_path.stem + ".webp"
                output_path = webp_folder / output_name
                result = self.convert_to_webp(img_path, output_path, 200)
                convert_count[0] += 1
                self.root.after(0, self.update_convert_progress, convert_count[0], len(downloaded_files))
                if result:
                    return result
                return None
            
            with ThreadPoolExecutor(max_workers=convert_threads) as executor:
                futures = [executor.submit(convert_with_progress, path) for path in downloaded_files]
                for future in futures:
                    result = future.result()
                    if result:
                        webp_files.append(result)
            
            self.root.after(0, self.log, f"转换完成: {len(webp_files)}/{len(downloaded_files)}")
            
            # 生成txt文件
            if webp_files:
                # 获取用户自定义的URL前缀
                base_url = self.base_url_entry.get().strip()
                if not base_url.endswith('/'):
                    base_url += '/'
                
                txt_filename = target_folder / f"{folder_name}.txt"
                
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    for webp_file in sorted(webp_files):
                        full_url = base_url + webp_file
                        f.write(full_url + '\n')
                
                self.root.after(0, self.log, f"✓ 已生成文件列表: {txt_filename.name}")
                self.root.after(0, self.log, f"  URL前缀: {base_url}")
            
            self.root.after(0, self.log, f"✓ 任务完成: {folder_name}")
            
        except Exception as e:
            self.root.after(0, self.log, f"✗ 任务失败: {str(e)}")
    
    def download_image(self, url, save_path, headers, max_retries=3):
        """下载单张图片"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return False
        return False
    
    def convert_to_webp(self, input_path, output_path, max_size_kb=200):
        """转换图片为webp格式"""
        try:
            img = Image.open(input_path)
            
            # 转换RGBA为RGB
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 压缩
            quality = 90
            while quality > 10:
                buffer = BytesIO()
                img.save(buffer, format='WEBP', quality=quality)
                size_kb = buffer.tell() / 1024
                
                if size_kb <= max_size_kb or quality <= 20:
                    with open(output_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    return os.path.basename(output_path)
                
                quality -= 5
            
            return None
        except Exception as e:
            return None
    
    def start_processing(self):
        """开始处理按钮回调 - 已废弃，使用批量解析"""
        messagebox.showinfo("提示", "请使用上方的【批量解析】按钮\n输入网址后自动完成解析、下载和转换")

def main():
    root = tk.Tk()
    app = ImageDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
