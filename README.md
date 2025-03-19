# Ban XunLei

让你的qBittorrent远离吸血雷。


## 简介

本项目是一个用于扫描 qBittorrent 客户端中连接的 Peer(客户端) 并自动禁止可疑 Peer 的 Python 脚本。它通过 qBittorrent 的 WebAPI 获取当前活动的种子及其连接的 Peer 信息，并根据一系列规则检测可疑的 Peer（如迅雷客户端、使用高风险端口的 Peer 等），并自动禁止这些 Peer。

## 功能

- **自动检测迅雷客户端**：检测并禁止使用迅雷客户端的 Peer.
- **高风险端口检测**：检测并禁止使用高风险端口的 Peer.
- **上传行为检测**：检测 Peer 的上传行为，禁止那些上传量为0但下载量异常的 Peer.
- **定时扫描**：每隔一段时间自动扫描一次（默认20s），确保实时监控。

## 依赖

- Python 3.x
  - `urllib` 库（Python 标准库）
  - `json` 库（Python 标准库）
  - `time` 库（Python 标准库）
  - `base64` 库（Python 标准库）

## 配置

在使用之前，请确保正确配置以下信息：

1. **WEB_URL**：qBittorrent WebUI 的地址，默认为 `http://127.0.0.1:8080/`，请根据实际情况修改。
2. <del> **USERNAME** 和 **PASSWORD**：如果 qBittorrent WebUI 启用了认证，请填写用户名和密码。切勿在公共设备上存储明文密码。</del> <br>由于目前发现无法通过WEBUI的认证机制，建议本地部署时在qBittorrent WebUI 设置中勾选 **对本地主机上的客户端跳过身份验证** 选项。 

有以下两种配置方法：
### 1. 环境变量
   
   #### 临时配置：
   
   ##### Linux (bash)
   ```bash
    export QBT_URL=""       
    # 在引号之间填入WEBUI的URL，务必以“/”结尾。如："http://127.0.0.1:8080/"
    export QBT_USERNAME="" 
    # 在引号之间填入用户名
    export QBT_PASSWD=""    
    # 在引号之间填入密码
   ```
   ##### 或对于Windows (Powershell)
   ```pwsh
   $env:QBT_URL=""
    # 在引号之间填入WEBUI的URL，务必以“/”结尾。如："http://127.0.0.1:8080/"
   $env:QBT_USERNAME=""
    # 在引号之间填入用户名 
   $env:QBT_PASSWD=""
    # 在引号之间填入密码
   ```
   #### 长期配置
   ##### Linux
--- 
TBW

### 2. 配置文件
配置文件名为`config.json`，在`babxunlei.py`的同一目录下即可。
```json
{
    "webui" : {
        "url"       :   "" , 
        //  在引号之间填入WEBUI的URL，务必以“/”结尾。如："http://127.0.0.1:8080/"
        "username"  :   "",
        //  在引号之间填入用户名 
        "passwd"    :   ""
        //  在引号之间填入密码
    }
    ,
    "config" : {
        "sleeptime" :   "",
        "tolerate_upspeed"  :   "",
        "safe_upspeed"  :    ""
    } 
    ,
    
     "leech_clients":  [
        // 已内置部分报道的吸血客户端，默认风险分+3
     ]
    }
    
}
```

**<big>优先级按照 `环境变量`>`config.json`>`默认值` 排列。修改配置文件后请检查环境变量是否有冲突配置。**

以上两种方法如无其他说明也可适用于其他自定义配置。

## 使用方法

1. **克隆或下载项目**：将`banxunlei.py`下载到本地。
2. **配置信息**：修改 `WEB_URL`、`USERNAME` 和 `PASSWORD` 为你的 qBittorrent WebUI 的实际信息。
3. **运行脚本**：在终端或命令行中运行脚本。

```bash
python banxunlei.py
```

4. **查看输出**：脚本会定期扫描并输出检测到的可疑 Peer 信息，并自动禁止高风险 Peer。

## 代码结构

- **create_auth_header()**：生成用于认证的 HTTP 头。
- **check_api_version()**：检查 qBittorrent WebAPI 的版本，确保兼容性。
- **fetch_data(api_endpoint)**：从指定的 API 端点获取数据。
- **convert_peers_format(peer_info)**：将 Peer 信息转换为适合 API 请求的格式。
- **ban_peer(peer_info)**：禁止指定的 Peer。
- **主循环**：定期扫描活跃种子及其连接的 Peer，并根据规则禁止可疑 Peer。

## 判定规则
对于每个 peer，初始赋予一个风险评分 `score = 0` ，并获取该节点的客户端信息、IP地址和端口号，并按照如下逻辑进行打分：

- **客户端名称检测。** 检测是否包含迅雷相关的关键词（如xl、xunlei、thunder）。如果检测到迅雷客户端，风险评分`score`会加2分。   
- **端口检测。** 检查peer的端口号是否在预定义的 **可疑端口** 列表中。如果端口号匹配，则根据端口号的风险等级增加相应的分数。例如，`15000` 是迅雷的默认端口；其他端口如12345、2011等会增加1分。
- **上传行为检测。** 代码会检查peer的上传行为。如果节点的下载进度（progress）为0，但已经向其上传了大量数据（默认阈值是超过16MB和64MB），则认为该节点存在可疑行为，并增加相应的分数。

如果peer的风险评分`score`大于等于2，则调用 `ban_peer` 函数禁止该节点。如果禁止成功，则输出`[已禁止]`；如果禁止失败，则输出`[禁止失败]`和错误信息。

如果风险评分大于0但小于2，则输出`[可疑]`，表示该节点存在一定的风险，但尚未达到禁止的阈值。

## 注意事项

- **API 版本**：确保 qBittorrent 的版本 ≥ v4.1.0，否则脚本可能无法正常工作。
- **认证失败**：如果认证失败，请检查 `USERNAME` 和 `PASSWORD` 是否正确。

## 自定义用法

- **自定义高风险端口**：可按需修改 `suspicious_ports` 中的端口及其对应的风险分数。
- **自定义客户端** 修改`config.json`中的`leech_clients`数组即可。以下为内置的客户端：
```json
"leech_clients":  [
        "dt/torrent",
        "Taipei-Torrent",
        "taipei-torrent",
        "BitComet 2.04",
        "hp/torrent",
        "github.com/anacrolix/torrent",
        "Transaction 2.94",
        "TrafficConsume"
     ]
```
- **自定义风险评分** 在源码中修改与 `score` 相关的数值即可。
- **自定义扫描时间** 修改环境变量`'BANXL_SLEEPTIME'`或者修改`config.json`中的`config.tolerate_upspeed`。
- **自定义可疑客户端下载速度封禁阈值** 
  - 可容忍的可疑客户端速度`tolerare_upspeed`：修改环境变量`'QBT_OKUPSPEED'`或者修改`config.json`中的`config.tolerate_upspeed`。默认值为1024 * 1024 * 1 = 1 MBps，风险评分减1。
  - 安全的可疑客户端速度`safe_upspeed`：修改环境变量`'QBT_SAFEUPSPEED'`或者修改`config.json`中的`config.safe_upspeed`。默认值为1024 * 1024 * 0.1 = 0.1 MBps，风险评分减2。

## 示例输出

```
[系统信息] qBittorrent WebAPI 版本: 2.11.2

========================================
开始扫描 (Sun Mar  9 19:11:27 2025)

扫描种子: ABCDEFG
本轮扫描完成，下次扫描将在20秒后开始
```

## 贡献

欢迎提交 Issue 或 Pull Request 来改进本项目。

## TODO LIST
- [x] 从环境变量和config.json获取配置
- [ ] 通过WEBUI的登录验证
- [ ] 添加英文版本
- [ ] 打包成二进制文件
- [ ] 添加GUI（？也许）
- [ ] 以服务加载
- ……


## 许可证

<p>
  <img src="WTFPL_logo.svg" alt="WTFPL Logo" width="100" style="vertical-align: middle;" />
  <span style="vertical-align: middle;">本项目采用 <a href="http://www.wtfpl.net/">WTFPL 许可证</a>。详情请参阅 <a href="/LICENSE">LICENSE</a> 文件。</span>
</p>

<big>**DO WHAT THE F\*\*K YOU WANT TO**</big>