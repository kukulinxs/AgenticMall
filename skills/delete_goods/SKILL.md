---
name: delete_goods
description: 删除商品。根据商品 ID 删除商品，操作需要管理员权限。
skill_name: delete_goods
display_name: 删除商品
trigger_keywords: ["删除商品", "移除商品", "删除"]
mcp_endpoint: http://127.0.0.1:8082/mcp/invoke
request_headers:
  X-Demo-Token: ${TELEAGENT_DEMO_TOKEN}
parameters:
  - name: goods_id
    type: string
    required: true
    description: 商品 ID
---

识别删除意图后收集 `goods_id`。缺少时只追问商品 ID，不得调用网关。获得 ID 后发送 `skill_name=delete_goods`。成功时确认删除，商品不存在或权限不足时按错误码反馈。
