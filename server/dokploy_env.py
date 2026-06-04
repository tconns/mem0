"""Dokploy / gateway overrides — file riêng, không có trên upstream.

Sau khi sync repo gốc mem0, chỉ cần giữ file này + 2 dòng hook trong main.py.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional


def _env(name: str) -> Optional[str]:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _set_base_url(block: Dict[str, Any], url: Optional[str]) -> None:
    if url:
        block["openai_base_url"] = url.rstrip("/")


def _normalize_qdrant_url(url: str) -> str:
    """Traefik TLS on :443; Qdrant container is plain HTTP on :6333 — drop :6333 for https URLs."""
    url = url.rstrip("/")
    if url.startswith("https://") and re.search(r":6333(?:/|$)", url):
        url = re.sub(r":6333(?=/|$)", "", url)
    return url


def _apply_qdrant_vector_store(config: Dict[str, Any]) -> bool:
    qdrant_url = _env("QDRANT_URL")
    qdrant_host = _env("QDRANT_HOST")
    qdrant_port = _env("QDRANT_PORT")
    qdrant_key = _env("QDRANT_API_KEY")

    if qdrant_url:
        if not qdrant_key:
            return False
        qdrant_config: Dict[str, Any] = {
            "url": _normalize_qdrant_url(qdrant_url),
            "api_key": qdrant_key,
        }
    elif qdrant_host and qdrant_port:
        qdrant_config = {
            "host": qdrant_host,
            "port": int(qdrant_port),
        }
        if qdrant_key:
            qdrant_config["api_key"] = qdrant_key
    else:
        return False

    dims = _env("QDRANT_EMBEDDING_DIMS")
    qdrant_config["collection_name"] = _env("QDRANT_COLLECTION") or "memories"
    qdrant_config["embedding_model_dims"] = int(dims) if dims else 1536

    config["vector_store"] = {"provider": "qdrant", "config": qdrant_config}
    return True


def apply_dokploy_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    openai_api_key = _env("OPENAI_API_KEY")
    openai_base_url = _env("OPENAI_BASE_URL")
    embedder_api_key = _env("EMBEDDER_API_KEY") or openai_api_key
    embedder_base_url = _env("OPENAI_EMBEDDING_BASE_URL") or openai_base_url

    if not _apply_qdrant_vector_store(config):
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
