---
name: query_goods
description: 查询商品。可查询全部商品，也可按商品 ID、名称、部门或上下架状态筛选。
skill_name: query_goods
display_name: 查询商品
trigger_keywords: ["查询商品", "查看商品", "商品列表", "查库存"]
mcp_endpoint: http://127.0.0.1:8082/mcp/invoke
request_headers:
  X-Demo-Token: ${TELEAGENT_DEMO_TOKEN}
parameters:
  - name: goods_id
    type: string
    required: false
    description: 商品 ID；指定时优先查询该商品
  - name: name
    type: string
    required: false
    description: 商品名称关键字
  - name: department
    type: string
    required: false
    description: 部门关键字
  - name: status
    type: string
    required: false
    enum: [online, offline]
    description: 上下架状态
---

查询不需要必填参数，用户未给筛选条件时查询全部商品。发送 `skill_name=query_goods`、可用筛选项和 `session_id`。成功时用清晰列表展示商品 ID、名称、价格、库存和状态；失败时按错误码反馈，且不展示 token 或原始错误。
