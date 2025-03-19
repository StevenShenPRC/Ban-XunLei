from urllib import parse, request
from urllib.parse import unquote, quote
import os
import json
import time
from base64 import b64encode

# API端点（严格小写）
SYNC_MAINDATA = "api/v2/sync/maindata"
SYNC_TORRENT_PEERS = "api/v2/sync/torrentPeers?hash="
TRANSFER_BANPEERS = "api/v2/transfer/banPeers"

# 认证处理
# 目前暂未解决
# def create_auth_header():
#     credential = b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode("utf-8")
#     return {"Authorization": f"Basic {credential}"}

# headers = create_auth_header()

# 获取配置信息
def get_config_value(env_var_name, config_key, default_value):
    """
    获取配置值，优先级：环境变量 > 配置文件 > 默认值
    :param env_var_name: 环境变量名称
    :param config_key: 配置文件中的键（例如 'database.url'）
    :param default_value: 默认值
    :return: 配置值
    """
    # 1. 尝试从环境变量获取
    value = os.getenv(env_var_name)
    if value:
        # 根据 default_value 的类型进行类型转换
        if isinstance(default_value, bool):
            # 处理布尔类型
            return value.lower() in ('true', '1', 't', 'y', 'yes')
        elif isinstance(default_value, int):
            return int(value)
        elif isinstance(default_value, float):
            return float(value)
        elif isinstance(default_value, str):
            return value
        else:
            # 如果 default_value 是其他类型，直接返回字符串
            return value

    # 2. 尝试从配置文件获取
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # 支持嵌套键（例如 'database.url'）
        keys = config_key.split('.')
        current = config
        for key in keys:
            current = current.get(key)
            if current is None:
                break
        
        if current:
            # 根据 default_value 的类型进行类型转换
            if isinstance(default_value, bool):
                # 处理布尔类型
                if isinstance(current, str):
                    return current.lower() in ('true', '1', 't', 'y', 'yes')
                else:
                    return bool(current)
            elif isinstance(default_value, int):
                return int(current)
            elif isinstance(default_value, float):
                return float(current)
            elif isinstance(default_value, str):
                return str(current)
            else:
                # 如果 default_value 是其他类型，直接返回 current
                return current
            
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass  # 配置文件不存在或格式错误，忽略

    # 3. 使用默认值
    return default_value

# 配置信息
WEB_URL = get_config_value(
    env_var_name='QBT_URL',
    config_key='webui.url',
    default_value='http://127.0.0.1:8080/'
)       # 获取WEBUI的url
USERNAME =get_config_value(
    env_var_name='QBT_USERNAME',
    config_key='webui.username',
    default_value=''
) # 此处获取用户名（如有，默认为空）
PASSWORD = get_config_value(
    env_var_name='QBT_PASSWD',
    config_key='webui.passwd',
    default_value=''
) # 此处获取密码（如有，默认为空）请配置环境变量或写入config.json, 切勿在公共设备上明文存储密码。
SLEEPTIME = get_config_value(
    env_var_name='BANXL_SLEEPTIME',
    config_key='config.sleeptime',
    default_value= 20
) # 此处获取循环间隔时间

def check_api_version():
    try:
        req = request.Request(
            url=WEB_URL + "api/v2/app/webapiVersion",
            # headers=headers
            # auth问题暂未解决
        )
        with request.urlopen(req) as res:
            print(f"[系统信息] qBittorrent WebAPI 版本: {res.read().decode()}")
    except Exception as e:
        print(f"[严重错误] API检测失败: {str(e)}")
        print("可能原因：")
        print("1. WebUI地址错误 → 当前值:", WEB_URL)
        print("2. 认证失败 → 用户:", USERNAME)
        print("3. qBittorrent版本过低（需 ≥ v4.1.0）")
        exit(1)

def fetch_data(api_endpoint):
    try:
        req = request.Request(
            url=WEB_URL + api_endpoint,
            # headers=headers
            # auth问题暂未解决
        )
        with request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode())
    except Exception as e:
        print(f"请求错误: {str(e)}")
        return None

def convert_peers_format(peer_info):
    # 分割哈希和peers部分
    hash_part, peers_part = peer_info.split('&', 1)
    
    # 处理peers参数
    encoded_peers = peers_part.split('=', 1)[1]
    decoded_peers = unquote(encoded_peers).strip('"')
    ip, port = decoded_peers.rsplit(':', 1)
    
    # 重构并编码
    formatted = f'[{ip}]:{port}'
    new_peers = quote(formatted, safe='')
    
    return f'{hash_part}&peers={new_peers}'

def ban_peer(peer_info):
    try:
        
        # 分割IP:Port（兼容IPv6）
        if peer_info.count(':') > 1:  # IPv6地址
            ip, port = peer_info.rsplit(':', 1)
            formatted_peer = f"[{ip}]:{port}"
        else:  # IPv4地址
            formatted_peer = peer_info
        
       
        # 构建POST数据
        post_data = "hash=" + torrent_hash +"&peers=" + quote(formatted_peer)
        
       
        # 发送请求
        req = request.Request(
            url=WEB_URL + TRANSFER_BANPEERS, 
            data=post_data.encode('utf-8'),
            method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
       
        
        with request.urlopen(req, timeout=5) as res:
            if res.status == 200:
                return True
            print(f"禁止失败，HTTP状态码: {res.status}")
            return False
            
    except Exception as e:
        print(f"处理异常: {str(e)}")
        return False
# 初始化检查
check_api_version()

while True:
    start_time = time.time()
    print("\n" + "="*40)
    print(f"开始扫描 ({time.asctime()})")
    
    main_data = fetch_data(SYNC_MAINDATA)
    if not main_data or 'torrents' not in main_data:
        print("无活跃种子，跳过扫描")
        time.sleep(SLEEPTIME)
        continue

    for torrent_hash in main_data['torrents']:
        peers_data = fetch_data(SYNC_TORRENT_PEERS + torrent_hash)
        if not peers_data or 'peers' not in peers_data:
            continue

        torrent_name = main_data['torrents'][torrent_hash].get('name', '未知种子')
        print(f"\n扫描种子: {torrent_name}")

        for peer_id, peer_info in peers_data['peers'].items():
            score = 0
            client = peer_info.get('client', '').lower()
            ip = peer_info.get('ip', '未知IP')
            port = peer_info.get('port', 0)

            # 客户端检测（支持多种迅雷变体）
            thunder_clients = ['xl', 'xunlei', 'thunder']
            if any(c in client for c in thunder_clients):
                print(f"检测到迅雷客户端: {peer_info.get('client') or '未知客户端'}")
                score += 2

            # 禁止其他配置的客户端
            leech_clients = get_config_value(
                env_var_name = '',
                config_key = 'leech_clients', 
                default_value = []
                )
            if any(c in client for c in leech_clients):
                print(f"检测到报道的吸血客户端: {peer_info.get('client') or '未知客户端'}")
                score += 3

            # 端口检测        
            suspicious_ports = {
                15000: 2,   # 默认高风险端口
                12345: 1,
                2011: 1,
                2013: 1,
                54321: 1
            }
            score += suspicious_ports.get(port, 0)

            # 上传行为检测 
            if peer_info.get('progress', 1) == 0 and peer_info.get('uploaded', 0) > 1024 * 1024 * 16:
                score += 1
            if peer_info.get('progress', 1) == 0 and peer_info.get('uploaded', 0) > 1024 * 1024 * 64:
                score += 2

            #上传速度检测
            MB = 1024 * 1024
            KB = 1024
            tolerate_upspeed = get_config_value(
                env_var_name = 'QBT_OKUPSPEED',
                config_key = 'config.tolerate_upspeed',
                default_value= int(1 * MB)
            )
            safe_upspeed = get_config_value(
                env_var_name = 'QBT_SAFEUPSPEED',
                config_key = 'config.safe_upspeed',
                default_value= int(100 * KB)
            )
            peer_upspeed = peer_info.get('up_speed', 0)
            if peer_upspeed < int(safe_upspeed):
                score -= 2
            elif peer_upspeed < int(tolerate_upspeed):
                score -= 1

            # 执行禁止
            if score >= 2:
                peer_str = f"{ip}:{port}"
                if ban_peer(peer_str):
                    print(f"[已禁止] {peer_str} | 客户端: {peer_info.get('client') or '未知'}")
                else:
                    print(f"[禁止失败] {peer_str}")
            elif score > 0:
                print(f"[可疑] {ip}:{port} | 客户端: {peer_info.get('client') or '未知'}")

    # 计算实际间隔时间
    elapsed = time.time() - start_time
    sleep_time = max(SLEEPTIME - elapsed, 1)
    while sleep_time > 0:
        print(f"\r本轮扫描完成，下次扫描将在{sleep_time:1.0f}秒后开始", end="", flush=True) 
        time.sleep(1)
        sleep_time -= 1
        if sleep_time < 0:  # 防止 sleep_time 变成负数
            sleep_time = 0
    time.sleep(sleep_time)