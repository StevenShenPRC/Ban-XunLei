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

1. **WEB_URL**：qBittorrent WebUI 的地址，默认为 `http://127.0.0.1:12345/`，请根据实际情况修改。
2. **USERNAME** 和 **PASSWORD**：如果 qBittorrent WebUI 启用了认证，请填写用户名和密码。切勿在公共设备上存储明文密码。建议本地部署时勾选 **对本地主机上的客户端跳过身份验证** 选项。

```python
WEB_URL = "http://127.0.0.1:1432/"  # 修改你的端口号，url必须以斜杠结尾
USERNAME = "" # 此处填写用户名（如有）
PASSWORD = "" # 此处填写密码（如有）切勿在公共设备上存储明文密码
```

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
- **自定义客户端** 可根据源码按需修改添加。
- **自定义分数** 在源码中修改与 `score` 相关的数值即可。
- **自定义扫描时间** 修改下面两段代码中的sleep时间即可。
```python
if not main_data or 'torrents' not in main_data:
        print("无活跃种子，跳过扫描")
        time.sleep(20)   #修改这里的20
        continue
```
```python
 # 计算实际间隔时间
    elapsed = time.time() - start_time
    sleep_time = max(20 - elapsed, 1)   #修改这里的20
    while sleep_time > 0:
        print(f"\r本轮扫描完成，下次扫描将在{sleep_time:1.0f}秒后开始", end="", flush=True) 
        time.sleep(1)
        sleep_time -= 1
        if sleep_time < 0:  # 防止 sleep_time 变成负数
            sleep_time = 0
    time.sleep(sleep_time)
```
   
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
- 添加英文版本
- ……


## 许可证

<p>
  <img src="WTFPL_logo.svg" alt="WTFPL Logo" width="100" style="vertical-align: middle;" />
  <span style="vertical-align: middle;">本项目采用 <a href="http://www.wtfpl.net/">WTFPL 许可证</a>。详情请参阅 <a href="/LICENSE">LICENSE</a> 文件。</span>
</p>

<big>**DO WHAT THE F\*\*K YOU WANT TO**</big>