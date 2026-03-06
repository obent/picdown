#!/usr/bin/env python3
"""
简易文件服务器
启动后列出当前目录下的所有文件，支持点击下载
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
from pathlib import Path
from urllib.parse import unquote
import mimetypes

class FileServerHandler(BaseHTTPRequestHandler):
    """文件服务器处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        # 解码URL
        path = unquote(self.path)
        
        # 移除开头的斜杠
        if path.startswith('/'):
            path = path[1:]
        
        # 如果路径为空，显示根目录
        if not path:
            self.list_directory('.')
            return
        
        # 检查文件是否存在
        if os.path.exists(path):
            if os.path.isfile(path):
                # 发送文件
                self.send_file(path)
            elif os.path.isdir(path):
                # 列出目录
                self.list_directory(path)
        else:
            self.send_error(404, "File Not Found")
    
    def list_directory(self, dir_path):
        """列出目录内容"""
        try:
            items = []
            
            # 获取目录中的所有项
            for item in sorted(os.listdir(dir_path)):
                item_path = os.path.join(dir_path, item)
                
                # 获取文件信息
                is_dir = os.path.isdir(item_path)
                size = 0 if is_dir else os.path.getsize(item_path)
                
                # 格式化大小
                if is_dir:
                    size_str = "[文件夹]"
                elif size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.2f} KB"
                elif size < 1024 * 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                
                # 构建链接 - 使用URL编码
                from urllib.parse import quote
                if dir_path == '.':
                    link = quote(item)
                else:
                    link = quote(os.path.join(dir_path, item))
                
                items.append({
                    'name': item,
                    'link': link,
                    'size': size_str,
                    'is_dir': is_dir
                })
            
            # 生成HTML
            html = self.generate_html(dir_path, items)
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            print(f"✗ 目录列出错误: {dir_path} - {str(e)}")
            self.send_error(500, "Server Error")
    
    def send_file(self, file_path):
        """发送文件"""
        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 猜测MIME类型
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # 获取文件名并进行URL编码
            filename = os.path.basename(file_path)
            # 使用RFC 5987编码文件名以支持中文
            from urllib.parse import quote
            encoded_filename = quote(filename)
            
            # 发送响应头
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(file_size))
            # 使用RFC 5987格式支持中文文件名
            self.send_header('Content-Disposition', f"attachment; filename*=UTF-8''{encoded_filename}")
            self.end_headers()
            
            # 发送文件内容
            with open(file_path, 'rb') as f:
                chunk_size = 8192
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            
            print(f"✓ 下载: {file_path} ({file_size} bytes)")
            
        except Exception as e:
            print(f"✗ 文件读取错误: {file_path} - {str(e)}")
            self.send_error(500, "File Read Error")
    
    def generate_html(self, dir_path, items):
        """生成HTML页面"""
        # 面包屑导航
        breadcrumb = self.generate_breadcrumb(dir_path)
        
        # 文件列表
        file_list = ""
        for item in items:
            icon = "📁" if item['is_dir'] else "📄"
            file_list += f"""
            <tr>
                <td>{icon}</td>
                <td><a href="/{item['link']}">{item['name']}</a></td>
                <td>{item['size']}</td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件服务器 - {dir_path}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        .breadcrumb {{
            background: #f8f9fa;
            padding: 15px 30px;
            border-bottom: 1px solid #dee2e6;
            font-size: 14px;
            color: #6c757d;
        }}
        
        .breadcrumb a {{
            color: #667eea;
            text-decoration: none;
            margin: 0 5px;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #f1f3f5;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        a {{
            color: #667eea;
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .empty {{
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 14px;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📂 文件服务器</h1>
            <p>点击文件名即可下载</p>
        </div>
        
        <div class="breadcrumb">
            {breadcrumb}
        </div>
        
        <div class="content">
            {self.generate_table(file_list, items)}
        </div>
        
        <div class="footer">
            Python 简易文件服务器 | 当前目录: {os.path.abspath(dir_path)}
        </div>
    </div>
</body>
</html>
        """
        return html
    
    def generate_breadcrumb(self, dir_path):
        """生成面包屑导航"""
        if dir_path == '.':
            return '📍 当前位置: <a href="/">根目录</a>'
        
        parts = dir_path.split(os.sep)
        breadcrumb = '📍 当前位置: <a href="/">根目录</a>'
        
        current_path = ""
        for part in parts:
            current_path = os.path.join(current_path, part) if current_path else part
            breadcrumb += f' / <a href="/{current_path}">{part}</a>'
        
        return breadcrumb
    
    def generate_table(self, file_list, items):
        """生成文件列表表格"""
        if not items:
            return '<div class="empty">📭 此目录为空</div>'
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th style="width: 50px;"></th>
                    <th>文件名</th>
                    <th style="width: 150px;">大小</th>
                </tr>
            </thead>
            <tbody>
                {file_list}
            </tbody>
        </table>
        """
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server(port=8000):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, FileServerHandler)
    
    print("=" * 60)
    print("🚀 文件服务器已启动")
    print("=" * 60)
    print(f"📂 服务目录: {os.path.abspath('.')}")
    print(f"🌐 访问地址: http://localhost:{port}")
    print(f"🌐 局域网访问: http://{get_local_ip()}:{port}")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")

def get_local_ip():
    """获取本机IP地址"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    import sys
    
    # 获取端口号
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("错误: 端口号必须是数字")
            sys.exit(1)
    
    run_server(port)
