"""HTTP 層 — 画面（SCR）と帳票（RPT）。

ドメイン層（billing.py）の薄いラッパー。BillingError を HTTP 409 / 404 に変換する
（Design Spec 3.2）。業務ルールはこの層に書かない。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .billing import BillingError, BillingService
from .reports import (
    ISSUER_NAME,
    ISSUER_REGISTRATION_NO,
    build_invoice_list_csv,
    invoice_view,
)

app = FastAPI(title="月次請求書発行", version="1.0.0")
service = BillingService()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _get(invoice_no: str):
    """請求を取得する。存在しなければ 404（Design Spec 3.2）。"""
    try:
        return service.get_invoice(invoice_no)
    except BillingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- 画面（SCR） -----------------------------------------------------------
@app.get("/invoices", response_class=HTMLResponse)
def screen_invoice_list(request: Request, year_month: Optional[str] = None):
    """SCR-001 請求一覧。"""
    invoices = [invoice_view(inv) for inv in service.list_invoices(year_month)]
    return templates.TemplateResponse(
        request=request,
        name="invoice_list.html",
        context={"invoices": invoices, "year_month": year_month},
    )


# --- 画面のデータ源（JSON。Design Spec 3.1） --------------------------------
# **宣言順が重要**: パスパラメータは "." にも一致するため、`/invoices/{invoice_no}` を
# 先に宣言すると `/invoices/INV-1.json` が invoice_no="INV-1.json" として
# そちらに吸われる。JSON のルートを先に宣言すること。
# この順序は tests/test_api.py::test_json_routes_are_declared_before_html_detail が固定している。
@app.get("/invoices.json")
def data_invoice_list(year_month: Optional[str] = None):
    return [invoice_view(inv) for inv in service.list_invoices(year_month)]


@app.get("/invoices/{invoice_no}.json")
def data_invoice_detail(invoice_no: str):
    return invoice_view(_get(invoice_no))


@app.get("/invoices/{invoice_no}", response_class=HTMLResponse)
def screen_invoice_detail(request: Request, invoice_no: str):
    """SCR-002 請求明細。"""
    return templates.TemplateResponse(
        request=request,
        name="invoice_detail.html",
        context={"inv": invoice_view(_get(invoice_no))},
    )


@app.get("/invoices/{invoice_no}/preview", response_class=HTMLResponse)
def screen_invoice_preview(request: Request, invoice_no: str):
    """SCR-003 請求書プレビュー。"""
    return templates.TemplateResponse(
        request=request,
        name="invoice_preview.html",
        context={"inv": invoice_view(_get(invoice_no))},
    )


# --- 帳票（RPT） -----------------------------------------------------------
@app.get("/invoices/{invoice_no}/report", response_class=HTMLResponse)
def report_invoice(request: Request, invoice_no: str):
    """RPT-001 請求書（印刷用 HTML）。適格請求書の記載事項を出力する（REQ-006）。"""
    return templates.TemplateResponse(
        request=request,
        name="report_invoice.html",
        context={
            "inv": invoice_view(_get(invoice_no)),
            "issuer_name": ISSUER_NAME,
            "issuer_registration_no": ISSUER_REGISTRATION_NO,
        },
    )


@app.get("/invoices.csv", response_class=PlainTextResponse)
def report_invoice_list_csv(year_month: Optional[str] = None):
    """RPT-002 請求一覧表（CSV）。"""
    return PlainTextResponse(
        build_invoice_list_csv(service.list_invoices(year_month)),
        media_type="text/csv; charset=utf-8",
    )


# --- 操作 ------------------------------------------------------------------
#: 操作者が指定されなかった場合の既定値
DEFAULT_ACTOR = "keiri01"


async def _read_actor(request: Request) -> str:
    """リクエストボディから操作者を読む。

    画面（SCR-003）は form post、プログラムからの呼び出しは JSON を送る。
    片方だけを受け付けると、もう片方は**黙って既定値になり**、監査ログ（REQ-010）に
    誤った操作者が記録される。どちらの形式でも受け取る。

    form は application/x-www-form-urlencoded のみを標準ライブラリで読む。
    python-multipart に依存しないため（ADR-0004）、multipart/form-data は 415 で拒否する。
    既定値で黙って確定させないためである。
    """
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/"):
        raise HTTPException(
            status_code=415,
            detail="multipart/form-data は受け付けません（form-urlencoded か JSON で送ってください）",
        )
    try:
        if content_type.startswith("application/json"):
            payload = await request.json()
        else:
            body = (await request.body()).decode("utf-8")
            payload = {k: v[0] for k, v in parse_qs(body).items()}
    except Exception:  # ボディ無し・壊れた JSON でも確定操作は続行する
        return DEFAULT_ACTOR

    actor = payload.get("actor") if hasattr(payload, "get") else None
    return str(actor) if actor else DEFAULT_ACTOR


@app.post("/invoices/{invoice_no}/confirm")
async def confirm_invoice(invoice_no: str, request: Request):
    """UC-006 請求の確定。"""
    _get(invoice_no)
    try:
        service.confirm(invoice_no, actor=await _read_actor(request))
    except BillingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RedirectResponse(url=f"/invoices/{invoice_no}", status_code=303)
