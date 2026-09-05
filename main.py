"""TeleAgent product operations demo: MCP-style gateway and mock backend."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Literal, Optional, Type
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Header
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


ONLINE = "online"
OFFLINE = "offline"
ADMIN_TOKEN = "demo-admin-token"
OPERATOR_TOKEN = "demo-operator-token"

PERMISSIONS = {
    "admin": {"add_goods", "query_goods", "update_goods", "change_status", "delete_goods"},
    "operator": {"query_goods", "change_status"},
}
TOKEN_ROLES = {ADMIN_TOKEN: "admin", OPERATOR_TOKEN: "operator"}


class Goods(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    department: str
    description: str
    status: Literal["online", "offline"]
    create_time: int


class MCPRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(min_length=1)
    parameters: Dict[str, Any]
    session_id: str = Field(min_length=1)
    role_id: Optional[str] = None


class AddGoodsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0, le=99999)
    department: str
    description: str = ""

    @field_validator("name", "department")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class QueryGoodsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goods_id: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[Literal["online", "offline"]] = None


class UpdateGoodsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goods_id: str = Field(min_length=1)
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0, le=99999)
    department: Optional[str] = None
    description: Optional[str] = None

    @field_validator("goods_id")
    @classmethod
    def goods_id_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("department")
    @classmethod
    def department_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ChangeStatusParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goods_id: str = Field(min_length=1)
    target_status: Literal["online", "offline"]

    @field_validator("goods_id")
    @classmethod
    def goods_id_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class DeleteGoodsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goods_id: str = Field(min_length=1)

    @field_validator("goods_id")
    @classmethod
    def goods_id_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


goods_db: Dict[str, Goods] = {}


def response(code: int, msg: str, data: Optional[Any] = None) -> Dict[str, Any]:
    return {"code": code, "msg": msg, "data": {} if data is None else data}


def success(data: Any) -> Dict[str, Any]:
    return response(0, "success", data)


def reset_mock_data() -> None:
    """Restore deterministic seed data whenever the process starts."""
    now = int(datetime.now(timezone.utc).timestamp())
    goods_db.clear()
    initial_goods = (
        Goods(id="g_001", name="华为Mate60", price=5999, stock=50, department="手机事业部", description="旗舰机型", status=ONLINE, create_time=now),
        Goods(id="g_002", name="联想ThinkPad X1", price=8999, stock=30, department="电脑事业部", description="商务笔记本", status=ONLINE, create_time=now),
        Goods(id="g_003", name="索尼WH-1000XM5", price=1999, stock=100, department="音频事业部", description="降噪耳机", status=OFFLINE, create_time=now),
    )
    for goods in initial_goods:
        goods_db[goods.id] = goods
    print("[System] 3 条演示数据初始化完成。")


def add_goods(params: AddGoodsParams) -> Dict[str, Any]:
    if any(goods.name == params.name for goods in goods_db.values()):
        return response(2005, "duplicate name")
    goods_id = f"g_{uuid4().hex[:6]}"
    goods_db[goods_id] = Goods(
        id=goods_id,
        name=params.name,
        price=params.price,
        stock=params.stock,
        department=params.department,
        description=params.description,
        status=ONLINE,
        create_time=int(datetime.now(timezone.utc).timestamp()),
    )
    return success({"goods_id": goods_id, "name": params.name})


def query_goods(params: QueryGoodsParams) -> Dict[str, Any]:
    if params.goods_id is not None:
        goods = goods_db.get(params.goods_id)
        return success([] if goods is None else [goods.model_dump()])
    result = list(goods_db.values())
    if params.name is not None:
        result = [goods for goods in result if params.name in goods.name]
    if params.department is not None:
        result = [goods for goods in result if params.department in goods.department]
    if params.status is not None:
        result = [goods for goods in result if params.status == goods.status]
    return success([goods.model_dump() for goods in result])


def update_goods(params: UpdateGoodsParams) -> Dict[str, Any]:
    goods = goods_db.get(params.goods_id)
    if goods is None:
        return response(2001, "goods not found")
    update_fields = params.model_fields_set - {"goods_id"}
    if not update_fields:
        return response(1001, "at least one update field is required")
    if "price" in update_fields:
        goods.price = params.price  # type: ignore[assignment]
    if "stock" in update_fields:
        goods.stock = params.stock  # type: ignore[assignment]
    if "department" in update_fields:
        goods.department = params.department  # type: ignore[assignment]
    if "description" in update_fields:
        goods.description = params.description  # type: ignore[assignment]
    return success({"goods_id": goods.id, "updated": True})


def change_status(params: ChangeStatusParams) -> Dict[str, Any]:
    goods = goods_db.get(params.goods_id)
    if goods is None:
        return response(2001, "goods not found")
    if params.target_status == ONLINE and goods.status == ONLINE:
        return response(2003, "already online")
    if params.target_status == OFFLINE and goods.status == OFFLINE:
        return response(2002, "already offline")
    goods.status = params.target_status
    return success({"goods_id": goods.id, "new_status": goods.status})


def delete_goods(params: DeleteGoodsParams) -> Dict[str, Any]:
    if params.goods_id not in goods_db:
        return response(2001, "goods not found")
    del goods_db[params.goods_id]
    return success({"goods_id": params.goods_id, "deleted": True})


SkillHandler = Callable[[Any], Dict[str, Any]]
SKILLS: Dict[str, tuple[Type[BaseModel], SkillHandler]] = {
    "add_goods": (AddGoodsParams, add_goods),
    "query_goods": (QueryGoodsParams, query_goods),
    "update_goods": (UpdateGoodsParams, update_goods),
    "change_status": (ChangeStatusParams, change_status),
    "delete_goods": (DeleteGoodsParams, delete_goods),
}


def validation_response(error: ValidationError) -> Dict[str, Any]:
    """Translate parameter validation into the published business-code contract."""
    details = error.errors()
    for detail in details:
        if detail["loc"] and detail["loc"][-1] == "stock" and detail.get("type") == "less_than_equal":
            return response(2004, "stock exceeds 99999")
    first = details[0]
    field = ".".join(str(part) for part in first["loc"])
    return response(1001, f"{field}: {first['msg']}")


def run_skill(skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    parameter_model, handler = SKILLS[skill_name]
    try:
        parsed_parameters = parameter_model.model_validate(parameters)
    except ValidationError as error:
        return validation_response(error)
    return handler(parsed_parameters)


def role_from_token(token: Optional[str]) -> Optional[str]:
    return TOKEN_ROLES.get(token)


def log_gateway(session_id: str, declared_role: Optional[str], resolved_role: Optional[str], skill_name: str, result: Dict[str, Any]) -> None:
    print(
        "[MCP] "
        f"session={session_id} declared_role={declared_role or '-'} "
        f"resolved_role={resolved_role or '-'} skill={skill_name}"
    )
    print(f"[MCP] result_code={result['code']}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    reset_mock_data()
    yield


app = FastAPI(title="TeleAgent Product Operations Demo", lifespan=lifespan)


@app.post("/api/shop/goods/add")
def add_goods_api(params: AddGoodsParams) -> Dict[str, Any]:
    return add_goods(params)


@app.get("/api/shop/goods/list")
def query_goods_api(goods_id: Optional[str] = None, name: Optional[str] = None, department: Optional[str] = None, status: Optional[Literal["online", "offline"]] = None) -> Dict[str, Any]:
    params = QueryGoodsParams(goods_id=goods_id, name=name, department=department, status=status)
    return query_goods(params)


@app.put("/api/shop/goods/update")
def update_goods_api(params: UpdateGoodsParams) -> Dict[str, Any]:
    return update_goods(params)


@app.put("/api/shop/goods/status")
def change_status_api(params: ChangeStatusParams) -> Dict[str, Any]:
    return change_status(params)


@app.delete("/api/shop/goods/delete")
def delete_goods_api(params: DeleteGoodsParams) -> Dict[str, Any]:
    return delete_goods(params)


@app.post("/mcp/invoke")
def mcp_invoke(request: MCPRequest, x_demo_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if request.skill_name not in SKILLS:
        result = response(1003, "unknown skill")
        log_gateway(request.session_id, request.role_id, None, request.skill_name, result)
        return result
    role = role_from_token(x_demo_token)
    if role is None or request.skill_name not in PERMISSIONS[role]:
        result = response(1002, "permission denied")
        log_gateway(request.session_id, request.role_id, role, request.skill_name, result)
        return result
    print(f"[MCP] authorization=PASS role={role}")
    result = run_skill(request.skill_name, request.parameters)
    log_gateway(request.session_id, request.role_id, role, request.skill_name, result)
    return result


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080)
