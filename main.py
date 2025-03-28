import uvicorn

from fastapi import FastAPI, Query, Header, Cookie, Body, Path, status, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse,PlainTextResponse

from typing import Annotated, Union, Optional, List, Dict, Any, TypeVar, Generic, Literal, Type, overload
from pydantic import BaseModel, Field
from enum import Enum

from pprint import pprint
import os
from datetime import datetime

from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI()
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app, include_in_schema=False)

class Metadata(BaseModel):
    creationTimestamp: Optional[str] = None  # 값이 없을 수도 있으므로 Optional 처리

class Spec(BaseModel):
    token: str
    audiences: List[str]

class StatusUser(BaseModel):
    # 추가 필드가 들어올 수 있으므로 Dict 사용 (빈 객체일 가능성 있음)
    extra: Optional[Dict[str, str]] = None
class Status(BaseModel):
    user: Optional[StatusUser] = Field(default_factory=StatusUser)  # 기본값 설정

class TokenReviewRequest(BaseModel):
    kind: str
    apiVersion: str
    metadata: Metadata
    spec: Spec
    status: Status

class TokenReviewResponse(BaseModel):
    kind: str
    apiVersion: str
    status: Dict


T = TypeVar("T", bound=BaseModel)
class Builder(Generic[T]):
    def __init__(self, model: type[T]):
        self._model = model
        self._data: Dict[str, Any] = dict()

    def set(self, key: str, value: Any) -> "Builder[T]":
        if key not in self._model.__annotations__:
            raise AttributeError(f"{key} is not valid")
        self._data[key] = value
        return self
    def build(self) -> T:
        return self._model(**self._data)





@app.get("/", response_class=PlainTextResponse)
def read_root(request: Request, x_forwarded_for: Union[str, None] = Header(default=None, convert_underscores=True) , body = Body):
    image_tag = os.getenv("TAG", "unknown")
    now = datetime.now()
    (client_ip, client_port) = request.client
    if x_forwarded_for:
        client_ip = x_forwarded_for
    request_url = request.url

    response= "This is test FastAPI server made by Zerotay!\n"
    response+= now.strftime("The time is %-I:%M:%S %p\n")
    response+= f"TAG VERSION: {image_tag}\n"
    response+= f"Server hostname: {request_url}\n"
    response+= f"Client IP, Port: {client_ip}:{client_port}\n"
    response+= "----------------------------------\n"
    return response

@app.post("/audit/")
async def fetch_audit(
    timeout: str, 
    # header: Union[str, None] = Header(default=None) , 
    body = Body,
    # request: Request
):
    print('this is timeout second of api server: ', timeout)

    # body: dict = json.load(io.BytesIO(await request.body()))
    pprint(body())
    return { }

@app.post("/auth/")
async def handle_auth(
    timeout: str, 
    request: TokenReviewRequest,
):
    print('this is timeout second of api server: ', timeout)
    pprint(request.model_dump())

    body = {
        "authenticated": True,
        "user": {
          "username": "test-ua",
          "uid": "42",
          "groups": ["developers", "qa"],
          "extra": {
            "extrafield1": [
              "extravalue1",
              "extravalue2"
            ]
          }
        },
        "audiences": ["https://kubernetes.default.svc.cluster.local"]
    }
    print(body)

    builder = Builder(TokenReviewResponse)
    response: TokenReviewResponse = (
        builder
        .set("kind", request.kind)
        .set("apiVersion", request.apiVersion)
        .set("status", body)
        .build()
    )
    return response



if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        port=80, 
        host='0.0.0.0', 
        reload=True, 
        # ssl_keyfile= 'pki/webhook.key',
        # ssl_certfile= 'pki/webhook.crt',
    )
