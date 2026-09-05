---
name: change_status
description: 上架或下架商品。根据商品 ID 将商品状态切换为 online 或 offline。
skill_name: change_status
display_name: 上下架商品
trigger_keywords: ["上架商品", "下架商品", "上架", "下架"]
mcp_endpoint: http://127.0.0.1:8082/mcp/invoke
request_headers:
  X-Demo-Token: ${TELEAGENT_DEMO_TOKEN}
parameters:
  - name: goods_id
    type: string
    required: true
    description: 商品 ID
  - name: target_status
    type: string
    required: true
    enum: [online, offline]
    description: online 为上架，offline 为下架
---

先收集 `goods_id` 和目标状态。缺少任一项时每次只追问一个字段，参数齐全后发送 `skill_name=change_status`。成功时反馈新状态；重复上架或下架时按对应错误码解释当前状态。
