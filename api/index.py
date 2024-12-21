# api/index.py
from flask import Flask, request, render_template, jsonify
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES
from urllib.parse import urlparse
import re
import os

# 修改模板文件夹的路径配置
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

# 调试模式，用于显示详细错误信息
app.debug = True

# 添加错误处理
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify(error=str(error)), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify(error="Not found"), 404

# 配置常量
KEY = b'Wxzxvpn2023key@$'
IV = b'Wxzxvpn2023key@$'
INSTITUTION = "webvpn.dlut.edu.cn"
SEGMENT_SIZE = 128

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_domain(domain):
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, domain))

def getCiphertext(plaintext, key=KEY, cfb_iv=IV, size=SEGMENT_SIZE):
    try:
        message = plaintext.encode('utf-8')
        cfb_cipher_encrypt = AES.new(key, AES.MODE_CFB, cfb_iv, segment_size=size)
        mid = cfb_cipher_encrypt.encrypt(message)
        return hexlify(mid).decode()
    except Exception as e:
        raise ValueError(f"加密过程出错: {str(e)}")

def getVPNUrl(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    if not is_valid_url(url):
        raise ValueError("无效的URL格式")

    try:
        parts = url.split('://')
        pro = parts[0]
        add = parts[1]
        
        hosts = add.split('/')
        domain_port = hosts[0].split(':')
        domain = domain_port[0]
        
        if not is_valid_domain(domain):
            raise ValueError("无效的域名格式")
        
        port = '-' + domain_port[1] if len(domain_port) > 1 else ''
        cph = getCiphertext(domain)
        fold = '/'.join(hosts[1:])
        
        key = hexlify(IV).decode('utf-8')
        return f'https://{INSTITUTION}/{pro}{port}/{key}{cph}/{fold}'
    
    except Exception as e:
        raise ValueError(f"URL转换失败: {str(e)}")

@app.route('/', methods=['GET'])
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f'Error rendering template: {e}')
        return f'Error rendering template: {e}', 500

@app.route('/api/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': '请输入URL'}), 400
            
        result = getVPNUrl(url)
        return jsonify({'result': result})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': '服务器内部错误，请稍后重试'}), 500

if __name__ == '__main__':
    app.run(debug=True)
