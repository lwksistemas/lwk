"""Serialização de EmailMessage para fila django-q."""
from __future__ import annotations

import base64
from typing import Any

from django.core.mail import EmailMessage, EmailMultiAlternatives


def _encode_attachment(filename: str, content, mimetype: str) -> dict[str, Any]:
    if isinstance(content, str):
        return {
            "filename": filename,
            "content": content,
            "mimetype": mimetype,
            "binary": False,
        }
    raw = bytes(content)
    return {
        "filename": filename,
        "content_b64": base64.b64encode(raw).decode("ascii"),
        "mimetype": mimetype,
        "binary": True,
        "size": len(raw),
    }


def serialize_email_message(msg: EmailMessage) -> dict[str, Any]:
    attachments = []
    total_bytes = 0
    for item in msg.attachments or []:
        if isinstance(item, tuple) and len(item) >= 2:
            filename = item[0]
            content = item[1]
            mimetype = item[2] if len(item) > 2 else "application/octet-stream"
            att = _encode_attachment(filename, content, mimetype)
            attachments.append(att)
            if att.get("binary"):
                total_bytes += att["size"]
            else:
                total_bytes += len(str(att["content"]).encode("utf-8"))

    alternatives = []
    if isinstance(msg, EmailMultiAlternatives):
        for content, mimetype in msg.alternatives:
            alternatives.append({"content": content, "mimetype": mimetype})
            total_bytes += len(str(content).encode("utf-8"))

    body = msg.body or ""
    total_bytes += len(body.encode("utf-8"))

    return {
        "subject": msg.subject or "",
        "body": body,
        "from_email": msg.from_email,
        "to": list(msg.to or []),
        "cc": list(msg.cc or []),
        "bcc": list(msg.bcc or []),
        "reply_to": list(msg.reply_to or []),
        "content_subtype": getattr(msg, "content_subtype", "plain"),
        "alternatives": alternatives,
        "attachments": attachments,
        "payload_bytes": total_bytes,
    }


def _build_email_kwargs(data: dict[str, Any]) -> dict[str, Any]:
    """Monta kwargs comuns para EmailMessage / EmailMultiAlternatives."""
    return {
        "subject": data.get("subject") or "",
        "body": data.get("body") or "",
        "from_email": data.get("from_email"),
        "to": data.get("to") or [],
        "cc": data.get("cc") or None,
        "bcc": data.get("bcc") or None,
        "reply_to": data.get("reply_to") or None,
    }


def deserialize_email_message(data: dict[str, Any]) -> EmailMessage:
    kwargs = _build_email_kwargs(data)
    alternatives = data.get("alternatives") or []
    if alternatives:
        msg: EmailMessage = EmailMultiAlternatives(**kwargs)
        for alt in alternatives:
            msg.attach_alternative(alt["content"], alt["mimetype"])
    else:
        msg = EmailMessage(**kwargs)
        subtype = data.get("content_subtype") or "plain"
        if subtype != "plain":
            msg.content_subtype = subtype

    for att in data.get("attachments") or []:
        content = base64.b64decode(att["content_b64"]) if att.get("binary") else att["content"]
        msg.attach(att["filename"], content, att.get("mimetype") or "application/octet-stream")

    return msg


def payload_too_large_for_queue(data: dict[str, Any], max_bytes: int) -> bool:
    return int(data.get("payload_bytes") or 0) > max_bytes
