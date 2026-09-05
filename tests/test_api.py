import unittest

from main import MCPRequest, mcp_invoke, reset_mock_data


class ProductOperationsApiTests(unittest.TestCase):
    def setUp(self):
        reset_mock_data()

    def invoke(self, skill_name, parameters, token="demo-admin-token", role_id=None):
        payload = {
            "skill_name": skill_name,
            "parameters": parameters,
            "session_id": "test-session",
        }
        if role_id is not None:
            payload["role_id"] = role_id
        headers = {} if token is None else {"X-Demo-Token": token}
        return mcp_invoke(MCPRequest(**payload), x_demo_token=headers.get("X-Demo-Token"))

    def test_admin_can_complete_all_five_skills(self):
        created = self.invoke(
            "add_goods",
            {"name": "测试商品", "price": 10, "stock": 2, "department": "测试部"},
        )
        self.assertEqual(created["code"], 0)
        goods_id = created["data"]["goods_id"]

        queried = self.invoke("query_goods", {"goods_id": goods_id})
        self.assertEqual(queried["code"], 0)
        self.assertEqual(queried["data"][0]["name"], "测试商品")

        self.assertEqual(self.invoke("update_goods", {"goods_id": goods_id, "stock": 0})["code"], 0)
        self.assertEqual(self.invoke("change_status", {"goods_id": goods_id, "target_status": "offline"})["code"], 0)
        self.assertEqual(self.invoke("delete_goods", {"goods_id": goods_id})["code"], 0)
        self.assertEqual(self.invoke("query_goods", {"goods_id": goods_id})["data"], [])

    def test_operator_cannot_escalate_by_forging_role_id(self):
        response = self.invoke(
            "add_goods",
            {"name": "越权商品", "price": 10, "stock": 1, "department": "测试部"},
            token="demo-operator-token",
            role_id="admin",
        )
        self.assertEqual(response["code"], 1002)

    def test_unknown_skill_is_reported_before_authorization(self):
        response = self.invoke("not_a_skill", {}, token=None)
        self.assertEqual(response["code"], 1003)

    def test_business_exceptions_and_validation_codes(self):
        self.assertEqual(self.invoke("add_goods", {"name": "华为Mate60", "price": 1, "stock": 1, "department": "测试部"})["code"], 2005)
        self.assertEqual(self.invoke("delete_goods", {"goods_id": "g_999"})["code"], 2001)
        self.assertEqual(self.invoke("change_status", {"goods_id": "g_003", "target_status": "offline"})["code"], 2002)
        self.assertEqual(self.invoke("change_status", {"goods_id": "g_001", "target_status": "online"})["code"], 2003)
        self.assertEqual(self.invoke("add_goods", {"name": "库存异常", "price": 1, "stock": 100000, "department": "测试部"})["code"], 2004)
        self.assertEqual(self.invoke("update_goods", {"goods_id": "g_001"})["code"], 1001)

    def test_invalid_status_returns_parameter_error(self):
        response = self.invoke("change_status", {"goods_id": "g_001", "target_status": "pending"})
        self.assertEqual(response["code"], 1001)


if __name__ == "__main__":
    unittest.main()
