# TeleAgent 商品运维 Demo

这是一个单进程、内存存储的 TeleAgent 商品运维演示工程。它提供自研 MCP 风格 HTTP 网关和 Mock 商品后台，支持新增、查询、修改、上下架、删除五个商品技能。

## 环境与启动

需要 Python 3.9+ 和 [uv](https://docs.astral.sh/uv/)。

本机默认 uv 缓存目录存在冲突时，先在当前 PowerShell 会话设置项目内缓存：

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
```

```powershell
uv venv --python 3.13
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

开发时也可以使用：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8080
```

服务启动后访问 `http://127.0.0.1:8080/docs` 查看 Mock 后台和网关接口。若当前服务使用 `8082`，将示例 URL 中的端口替换为 `8082`。每次进程启动或 reload 都会恢复 3 条初始商品数据。

## 身份与权限

网关使用请求头 `X-Demo-Token` 在服务端解析身份。请求体内的 `role_id` 只写入日志，不能授权。

| Token | 角色 | 权限 |
| --- | --- | --- |
| `demo-admin-token` | admin | 五个商品技能 |
| `demo-operator-token` | operator | 查询、上下架 |

TeleAgent 使用管理员和运营两个独立配置，并分别保存 token。不要在对话中泄露 token。平台与本服务不在同一机器时，不能使用 `127.0.0.1`，需要填入平台可访问的地址。

## 网关调用示例

管理员新增商品：

```powershell
$headers = @{ "X-Demo-Token" = "demo-admin-token" }
$body = @{
  skill_name = "add_goods"
  session_id = "demo-admin-001"
  role_id = "untrusted-agent-role"
  parameters = @{
    name = "华为Mate70"
    price = 6999
    stock = 100
    department = "手机事业部"
    description = "旗舰"
  }
} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/mcp/invoke" -Headers $headers -ContentType "application/json" -Body $body
```

运营身份查询全部商品：

```powershell
$headers = @{ "X-Demo-Token" = "demo-operator-token" }
$body = @{ skill_name = "query_goods"; session_id = "demo-operator-001"; parameters = @{} } | ConvertTo-Json -Depth 3
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/mcp/invoke" -Headers $headers -ContentType "application/json" -Body $body
```

运营身份请求新增会返回 `{ "code": 1002, ... }`，即使请求体中伪造 `role_id: "admin"` 也不会获得管理员权限。

## TeleAgent 配置

五份可直接导入的技能模板在 [skills](./skills) 下，每个技能必须单独导入其子目录：

- `skills/add_goods/SKILL.md`
- `skills/query_goods/SKILL.md`
- `skills/update_goods/SKILL.md`
- `skills/change_status/SKILL.md`
- `skills/delete_goods/SKILL.md`

星辰智能体导入时，请选择 `skills/add_goods`、`skills/query_goods` 等**子目录**，不要选择外层 `skills` 目录。导入器要求所选目录的根部直接包含名为 `SKILL.md` 的文件。也可以将某个子目录压缩成 zip 后上传，但 zip 解压后的根部必须直接是 `SKILL.md`。

当前技能模板的网关地址为 `http://127.0.0.1:8082/mcp/invoke`。如果服务改回默认端口，请在导入前将五个 `SKILL.md` 中的 `8082` 统一改为 `8080`。

模板使用 `X-Demo-Token: ${TELEAGENT_DEMO_TOKEN}`。导入前，将其替换或映射为 TeleAgent 平台实际支持的密钥变量/自定义请求头写法；不同平台的 front matter 与 HTTP 工具定义可能不同。

## 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/mcp/invoke` | TeleAgent 的统一网关入口 |
| POST | `/api/shop/goods/add` | Mock 后台新增 |
| GET | `/api/shop/goods/list` | Mock 后台查询 |
| PUT | `/api/shop/goods/update` | Mock 后台修改 |
| PUT | `/api/shop/goods/status` | Mock 后台上下架 |
| DELETE | `/api/shop/goods/delete` | Mock 后台删除 |

网关已处理的业务结果均为 HTTP 200，并统一含有 `code`、`msg`、`data`。请求 JSON 的外层结构错误由 FastAPI 返回 HTTP 422。

## 自动化验证

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试不需要额外安装 pytest，覆盖全部技能、权限、异常码、库存边界和数据变更。
