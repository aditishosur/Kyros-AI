import os
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv("PULSEOPS_API_URL", "http://localhost:8000")


class PulseOpsAPIError(RuntimeError):
    pass


@st.cache_data(ttl=20, show_spinner=False)
def get_json(path: str) -> Any:
    try:
        response = requests.get(f"{API_BASE_URL}{path}", timeout=12)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise PulseOpsAPIError("Unable to reach PulseOps API. Check that the FastAPI service is running.") from exc


def post_json(path: str, payload: dict) -> Any:
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=12)
        response.raise_for_status()
        get_json.clear()
        return response.json()
    except requests.RequestException as exc:
        raise PulseOpsAPIError("Unable to reach PulseOps API. Check that the FastAPI service is running.") from exc


def put_json(path: str, payload: dict) -> Any:
    try:
        response = requests.put(f"{API_BASE_URL}{path}", json=payload, timeout=12)
        response.raise_for_status()
        get_json.clear()
        return response.json()
    except requests.RequestException as exc:
        raise PulseOpsAPIError("Unable to reach PulseOps API. Check that the FastAPI service is running.") from exc


def delete(path: str) -> None:
    try:
        response = requests.delete(f"{API_BASE_URL}{path}", timeout=12)
        response.raise_for_status()
        get_json.clear()
    except requests.RequestException as exc:
        raise PulseOpsAPIError("Unable to reach PulseOps API. Check that the FastAPI service is running.") from exc

