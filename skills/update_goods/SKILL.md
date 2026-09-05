---
name: update_goods
description: 修改商品。根据商品 ID 更新价格、库存、所属部门或商品描述。
skill_name: update_goods
display_name: 修改商品
trigger_keywords: ["修改商品", "更新商品", "修改价格", "修改库存"]
mcp_endpoint: http://127.0.0.1:8082/mcp/invoke
request_headers:
  X-Demo-Token: ${TELEAGENT_DEMO_TOKEN}
parameters:
  - name: goods_id
    type: string
    required: true
    description: 商品 ID
  - name: price
    type: number
    required: false
    description: 新价格，必须大于 0
  - name: stock
    type: integer
    required: false
    description: 新库存，范围为 0 至 99999
  - name: department
    type: string
    required: false
    description: 新所属部门
  - name: description
    type: string
    required: false
    description: 新商品描述
---

先收集 `goods_id`。随后必须至少收集一个待更新字段；若用户只提供商品 ID，追问要修改的内容。参数完整后发送 `skill_name=update_goods`。成功时确认更新，失败时按错误码反馈。
