---
name: add_goods
description: 新增商品。收集商品名称、价格、库存和所属部门后，通过 MCP 风格网关创建商品。
skill_name: add_goods
display_name: 新增商品
trigger_keywords: ["新增商品", "添加商品", "创建商品", "上架新品"]
mcp_endpoint: http://127.0.0.1:8082/mcp/invoke
request_headers:
  X-Demo-Token: ${TELEAGENT_DEMO_TOKEN}
parameters:
  - name: name
    type: string
    required: true
    description: 商品名称，不能与现有商品重复
  - name: price
    type: number
    required: true
    description: 商品价格（元），必须大于 0
  - name: stock
    type: integer
    required: true
    description: 库存，范围为 0 至 99999
  - name: department
    type: string
    required: true
    description: 所属部门
  - name: description
    type: string
    required: false
    description: 商品描述
---

识别新增商品意图后，依次收集 `name`、`price`、`stock`、`department`。缺少参数时，每次只追问第一个缺失参数，且不得调用网关。参数齐全后，向网关发送 `skill_name=add_goods`、`parameters`、`session_id`；不要发送或展示 token。成功时回复商品 ID，失败时按错误码转为中文说明。
