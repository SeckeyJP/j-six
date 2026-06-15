"""申請承認ワークフロー — HTTP API (FastAPI)

ドメインロジック（workflow.py）の薄いラッパー。WorkflowError を 409 に変換する。
逆生成設計書（Phase 6）はこの層と workflow.py から IF 設計書を生成する。
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .models import ApprovalRequest
from .workflow import WorkflowService, WorkflowError

app = FastAPI(title="申請承認ワークフロー API", version="1.0.0")
service = WorkflowService()


# --- スキーマ --------------------------------------------------------------
class CreateRequestBody(BaseModel):
    applicant: str = Field(..., description="申請者ID")
    amount: int = Field(..., description="申請金額（円）")
    title: str = Field(..., description="申請タイトル")
    approvers: list[str] = Field(..., description="承認者IDの順序付きリスト")


class ActorBody(BaseModel):
    actor: str = Field(..., description="操作者ID")
    note: str = Field("", description="コメント（任意）")


class AuditEntryView(BaseModel):
    action: str
    actor: str
    at: str
    note: str


class RequestView(BaseModel):
    id: str
    applicant: str
    amount: int
    title: str
    approvers: list[str]
    status: str
    current_step: int
    next_approver: Optional[str]
    audit_log: list[AuditEntryView]

    @classmethod
    def of(cls, req: ApprovalRequest) -> "RequestView":
        return cls(
            id=req.id,
            applicant=req.applicant,
            amount=req.amount,
            title=req.title,
            approvers=req.approvers,
            status=req.status.value,
            current_step=req.current_step,
            next_approver=req.next_approver,
            audit_log=[
                AuditEntryView(
                    action=e.action.value, actor=e.actor, at=e.at.isoformat(), note=e.note
                )
                for e in req.audit_log
            ],
        )


# --- エラー変換 ------------------------------------------------------------
def _guard(fn):
    try:
        return fn()
    except WorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# --- エンドポイント --------------------------------------------------------
@app.post("/requests", response_model=RequestView, status_code=201)
def create_request(body: CreateRequestBody) -> RequestView:
    req = _guard(
        lambda: service.create_request(
            body.applicant, body.amount, body.title, body.approvers
        )
    )
    return RequestView.of(req)


@app.get("/requests", response_model=list[RequestView])
def list_requests() -> list[RequestView]:
    return [RequestView.of(r) for r in service.list_all()]


@app.get("/requests/{request_id}", response_model=RequestView)
def get_request(request_id: str) -> RequestView:
    try:
        return RequestView.of(service.get(request_id))
    except WorkflowError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/requests/{request_id}/submit", response_model=RequestView)
def submit(request_id: str, body: ActorBody) -> RequestView:
    return RequestView.of(_guard(lambda: service.submit(request_id, body.actor)))


@app.post("/requests/{request_id}/approve", response_model=RequestView)
def approve(request_id: str, body: ActorBody) -> RequestView:
    return RequestView.of(_guard(lambda: service.approve(request_id, body.actor)))


@app.post("/requests/{request_id}/reject", response_model=RequestView)
def reject(request_id: str, body: ActorBody) -> RequestView:
    return RequestView.of(_guard(lambda: service.reject(request_id, body.actor, body.note)))


@app.post("/requests/{request_id}/remand", response_model=RequestView)
def remand(request_id: str, body: ActorBody) -> RequestView:
    return RequestView.of(_guard(lambda: service.remand(request_id, body.actor, body.note)))


@app.post("/requests/{request_id}/withdraw", response_model=RequestView)
def withdraw(request_id: str, body: ActorBody) -> RequestView:
    return RequestView.of(_guard(lambda: service.withdraw(request_id, body.actor)))
