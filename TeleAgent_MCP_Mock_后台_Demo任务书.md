# TeleAgent + 自研 MCP 风格网关 + Mock 后台 Demo 任务书

## 1. 目标与边界

### 1.1 目标

构建一个可演示的商品运维 Demo：TeleAgent 通过五个商品技能调用自研 HTTP 网关；网关在服务端完成技能校验、身份鉴权和业务转发；Mock 后台使用内存数据完成商品增、查、改、上下架、删。

演示须能证明以下能力：

- Agent 可补齐缺失参数后发起工具调用。
- 服务端可阻止无权限操作，且调用方不能通过伪造 `role_id` 越权。
- 成功、参数错误、权限错误、业务错误可返回稳定的结构化响应。
- 操作后的数据可以通过查询立即验证。

### 1.2 非目标

- 不接入真实数据库、真实商品后台、用户体系或生产级审计。
- 不实现标准 Model Context Protocol (MCP) 的 `tools/list`、`tools/call` 协议。
- 不处理多进程共享内存、分布式鉴权、持久化、并发事务。

本项目中的“自研 MCP”统一表述为“自研 MCP 风格 HTTP 网关”，避免与标准 MCP 协议混淆。

## 2. 技术栈与运行约束

| 项目 | 约定 |
| --- | --- |
| Python | Python 3.9+ |
| Web 框架 | FastAPI |
| ASGI 服务 | Uvicorn |
| 数据存储 | 进程内 `dict[str, Goods]` |
| 工程形态 | 单文件 `main.py`，业务函数和 HTTP 路由分层 |
| 端口 | 默认 `8080`，一个端口同一时刻仅运行一个服务实例 |
| 数据重置 | 每次服务进程启动时重新注入 3 条初始数据 |

`requirements.txt` 必须固定经验证的兼容范围，建议如下：

```text
fastapi>=0.110,<1.0
uvicorn[standard]>=0.27,<1.0
pydantic>=2,<3
```

### 2.1 启动与生命周期

初始数据必须通过 FastAPI `lifespan`（或 startup hook）加载，不得只放在 `if __name__ == "__main__"` 中。这样以下两种方式都能完成初始化：

```powershell
python main.py
uvicorn main:app --reload --port 8080
```

开发模式下 `--reload` 重启进程会重置内存数据，这是预期行为，README 必须明确说明。

### 2.2 部署可达性

在 TeleAgent 与网关运行于同一台机器时，技能端点可配置为 `http://127.0.0.1:8080/mcp/invoke`。若 TeleAgent 运行在云端，`localhost` 指向云端自身，必须使用平台可访问的部署地址或经批准的临时隧道地址。

## 3. 角色与身份模型

### 3.1 角色权限

| 服务端角色 | 可调用技能 |
| --- | --- |
| `operator` | `query_goods`、`change_status` |
| `admin` | `add_goods`、`query_goods`、`update_goods`、`change_status`、`delete_goods` |

### 3.2 身份来源

身份必须由网关服务端决定，**不得信任请求体中的 `role_id`**。Demo 使用请求头 `X-Demo-Token` 绑定角色：

| Token | 映射角色 |
| --- | --- |
| `demo-operator-token` | `operator` |
| `demo-admin-token` | `admin` |

请求中的 `role_id` 仅用于日志展示（可选字段），不参与授权。未知或缺失 token 返回 `1002`。

演示权限对比时，启动同一个服务，在两份 TeleAgent 配置中分别配置不同的 token；不要启动两个监听同一端口的服务。若平台不能配置自定义请求头，可改为服务端配置固定的 `DEMO_ROLE`，重启服务切换角色，但不得让 Agent 自行决定角色值。

## 4. 通用协议与错误码

### 4.1 网关请求

`POST /mcp/invoke`

```json
{
  "skill_name": "add_goods",
  "parameters": {
    "name": "华为Mate70",
    "price": 6999,
    "stock": 100,
    "department": "手机事业部",
    "description": "旗舰"
  },
  "session_id": "sess_12345",
  "role_id": "operator_001"
}
```

请求头：

```text
Content-Type: application/json
X-Demo-Token: demo-admin-token
```

`skill_name`、`parameters`、`session_id` 必填；`role_id` 可选且仅记录日志。请求 JSON 结构或字段类型不合法时，HTTP 返回 `422`。

### 4.2 网关响应

业务处理结果一律使用 HTTP `200`，响应结构固定如下：

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

网关未处理异常使用 HTTP `500`；响应仍应避免泄露堆栈、token 或内部实现细节。

### 4.3 业务错误码

| Code | 含义 | Agent 反馈模板 |
| --- | --- | --- |
| `0` | 成功 | 操作成功。{data} |
| `1001` | 参数缺失、类型或取值非法 | 参数不完整或不合法：{msg} |
| `1002` | 身份无效或权限不足 | 当前身份无此操作权限，请联系管理员。 |
| `1003` | 未知技能 | 暂不支持该操作。 |
| `2001` | 商品不存在 | 未找到对应 ID 的商品，请核对后重试。 |
| `2002` | 商品已下架 | 该商品当前已下架，无需重复操作。 |
| `2003` | 商品已上架 | 该商品当前已上架，无需重复操作。 |
| `2004` | 库存超出范围 | 库存必须是 0 到 99999 的整数。 |
| `2005` | 商品名称重复 | 系统中已存在同名商品，请修改名称。 |

校验顺序固定为：技能存在性 -> token/权限 -> 参数模型 -> 业务规则。这样未知技能不会被错误地报告为权限不足。

## 5. 商品模型与业务规则

```python
class Goods(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    department: str
    description: str
    status: Literal["online", "offline"]
    create_time: int
```

启动时加载以下数据：

| ID | 名称 | 价格 | 库存 | 部门 | 状态 |
| --- | --- | ---: | ---: | --- | --- |
| `g_001` | 华为Mate60 | 5999 | 50 | 手机事业部 | `online` |
| `g_002` | 联想ThinkPad X1 | 8999 | 30 | 电脑事业部 | `online` |
| `g_003` | 索尼WH-1000XM5 | 1999 | 100 | 音频事业部 | `offline` |

通用规则：

- 商品名称、所属部门去除首尾空格后不得为空；名称全局唯一。
- `price` 必须大于 `0`。
- `stock` 必须是 `0` 至 `99999` 的整数。
- 修改操作仅更新传入字段；`0` 与空字符串是合法的传入值，必须用 `is not None` 判断是否更新。
- `target_status` 只能为 `online` 或 `offline`。
- 删除成功后，后续查询中不应再出现该商品。

## 6. 五个技能契约

每个技能均由独立 Skill 文件配置，禁止以“其余类推”替代正式契约。

| skill_name | 权限 | 必填参数 | 可选参数 | 成功 `data` |
| --- | --- | --- | --- | --- |
| `add_goods` | admin | `name`, `price`, `stock`, `department` | `description` | `goods_id`, `name` |
| `query_goods` | operator/admin | 无 | `goods_id`, `name`, `department`, `status` | 商品数组 |
| `update_goods` | admin | `goods_id` | `price`, `stock`, `department`, `description` | `goods_id`, `updated` |
| `change_status` | operator/admin | `goods_id`, `target_status` | 无 | `goods_id`, `new_status` |
| `delete_goods` | admin | `goods_id` | 无 | `goods_id`, `deleted` |

`update_goods` 除 `goods_id` 外，至少应带一个可修改字段；否则返回 `1001`。`query_goods` 的 `goods_id` 查询优先级最高；其余字段采用 AND 过滤，`name` 与 `department` 使用包含匹配。

## 7. Skill 文件规范

交付五个可单独导入的技能目录：

```text
skills/
  add_goods/
    SKILL.md
  query_goods/
    SKILL.md
  update_goods/
    SKILL.md
  change_status/
    SKILL.md
  delete_goods/
    SKILL.md
```

星辰智能体导入时必须选择某一个技能子目录（例如 `skills/add_goods`），或上传该子目录压缩包；不得直接上传外层 `skills` 目录。所选目录的根部必须直接存在 `SKILL.md`，且 YAML front matter 至少包含 `name` 和 `description`。

每个文件应包含平台需要的 front matter、网关地址、请求头配置、参数类型和以下对话规则：

1. 识别对应意图后，按参数契约检查必填项。
2. 缺少必填项时不得调用网关；每次只追问一个当前缺失字段。
3. 参数齐全后，以 JSON 请求 `POST /mcp/invoke`，并携带所属环境的 `X-Demo-Token`。
4. `code == 0` 时根据技能输出简洁成功信息；否则按错误码表转为中文反馈。
5. 不得在对话中展示 token、内部地址、完整请求头或原始异常堆栈。

平台导入前必须确认其实际支持的 front matter、HTTP 工具调用格式和自定义请求头能力；若不支持，应在任务实现前调整适配方式，而不是假定示例 YAML 可直接运行。

## 8. 实现结构

虽然 Demo 保持单文件，但必须分层，避免由路由函数直接相互调用：

```text
main.py
  数据模型和响应模型
  内存仓储与初始化 lifespan
  商品业务函数（纯函数或服务类）
  Mock 后台路由：/api/shop/goods/*
  网关鉴权、技能映射与路由：/mcp/invoke
  日志配置
requirements.txt
skills/（5 个 Skill 文件）
README.md
tests/（可选但推荐）
```

Mock 后台路由和网关都调用同一组业务函数。网关不得通过 `await` 调用带 FastAPI 装饰器的路由处理器。

## 9. Mock 后台接口

| 方法与路径 | 作用 |
| --- | --- |
| `POST /api/shop/goods/add` | 新增商品 |
| `GET /api/shop/goods/list` | 查询商品；使用 query 参数筛选 |
| `PUT /api/shop/goods/update` | 更新商品 |
| `PUT /api/shop/goods/status` | 上架或下架 |
| `DELETE /api/shop/goods/delete` | 删除商品 |

这些接口用于手工验证和演示后台存在；其参数规则、响应结构与网关调用的业务规则必须一致。它们不取代网关鉴权能力，演示时应以 `/mcp/invoke` 为主路径。

## 10. 日志与安全约束

每次网关调用至少输出以下字段：时间、session_id、声明 role_id、服务端解析角色、skill_name、参数摘要、鉴权结论和业务响应码。

日志中不得输出 `X-Demo-Token`。商品描述过长时应截断。示例：

```text
[MCP] session=sess_12345 declared_role=operator_001 resolved_role=admin skill=add_goods
[MCP] authorization=PASS
[MCP] result_code=0
```

## 11. 标准演示流程

演示前启动一个服务实例，确认控制台显示“3 条演示数据初始化完成”。在 TeleAgent 中准备管理员和运营两个配置，分别携带管理员、运营 token。

1. 用运营配置说“帮我新增一个商品”。Agent 收集所需字段后，网关返回 `1002`。
2. 用管理员配置说“新增商品”。故意省略一个字段，验证 Agent 逐项追问；补齐后新增成功并获得 `g_xxx`。
3. 用管理员配置说“查询所有商品”，结果包含初始 3 条和刚新增商品。
4. 用管理员配置将 `g_001` 的价格改为 `4999`，再查询验证。
5. 请求删除 `g_999`，验证返回 `2001`。
6. 用运营配置请求下架 `g_003`，验证返回 `2002`。
7. 用管理员配置删除刚新增商品，再查询确认已删除。
8. 用运营配置请求删除 `g_001`，验证权限拦截。

若需回到初始数据，重启服务；不得同时在两个终端以同一端口启动服务。

## 12. 验收标准

| 分类 | 验收条件 |
| --- | --- |
| 启动 | `python main.py` 与 `uvicorn main:app --reload --port 8080` 均能加载初始数据并提供接口。 |
| 技能覆盖 | 五个 Skill 文件存在，五个技能均可通过网关成功调用。 |
| 权限 | 管理员拥有全部权限；运营仅有查询和状态变更权限；请求体伪造 `role_id=admin` 不能提升运营 token 权限。 |
| 参数校验 | 缺失必填项、空名称、非正价格、负库存、库存大于 99999、非法状态、空更新均返回 `1001` 或 `2004`。 |
| 业务异常 | 重名、商品不存在、重复上架、重复下架分别返回 `2005`、`2001`、`2003`、`2002`。 |
| 数据正确性 | 新增可查、更新可查、状态变更可查、删除后不可查。 |
| 响应 | 已处理业务请求响应含 `code`、`msg`、`data` 三个字段；错误码与本文档一致。 |
| 演示 | 第 11 节所有场景可在单服务实例下完成，日志可显示服务端解析角色和鉴权结论。 |

## 13. 交付物

- `main.py`
- `requirements.txt`
- `skills/` 下五份技能文件
- `README.md`：环境、启动命令、token 配置方式、curl 示例、数据重置说明
- `TeleAgent_MCP_Mock_后台_Demo任务书.md`（本文档）
- 推荐：`tests/` 下 API/业务规则自动化测试
