"""Dokploy / gateway overrides — file riêng, không có trên upstream.

Sau khi sync repo gốc mem0, chỉ cần giữ file này + 2 dòng hook trong main.py.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _env(name: str) -> Optional[str]:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _set_base_url(block: Dict[str, Any], url: Optional[str]) -> None:
    if url:
        block["openai_base_url"] = url.rstrip("/")


def apply_dokploy_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    openai_api_key = _env("OPENAI_API_KEY")
    openai_base_url = _env("OPENAI_BASE_URL")
    embedder_api_key = _env("EMBEDDER_API_KEY") or openai_api_key
    embedder_base_url = _env("OPENAI_EMBEDDING_BASE_URL") or openai_base_url

    app_db = _env("APP_DB_NAME")
    if app_db:
        config.setdefault("vector_store", {}).setdefault("config", {})["dbname"] = app_db

    llm = config.setdefault("llm", {}).setdefault("config", {})
    if openai_api_key:
        llm["api_key"] = openai_api_key
    _set_base_url(llm, openai_base_url)

    embedder = config.setdefault("embedder", {}).setdefault("config", {})
    if embedder_api_key:
        embedder["api_key"] = embedder_api_key
    _set_base_url(embedder, embedder_base_url)

    return config
