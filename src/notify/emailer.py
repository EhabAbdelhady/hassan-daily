"""Sends the daily preview and alert emails through Gmail SMTP or Resend."""

import base64
import html
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..config import settings

FROM_NAME = "HASSAN DAILY Bot"


def _price_rows(data: Optional[Dict[str, Any]]) -> str:
    if not data:
        return ""
    rows = []
    specs = [
        ("gold", "Gold 24k / 21k / 18k (EGP)", lambda d: f"{d['price_24k']} / {d['price_21k']} / {d['price_18k']}"),
        ("fx", "USD/EGP buy / sell", lambda d: f"{d['buy']} / {d['sell']}"),
        ("crypto", "Bitcoin (USD)", lambda d: d["price"]),
        ("oil", "Brent (USD/bbl)", lambda d: d["price"]),
    ]
    for key, label, fmt in specs:
        d = data.get(key)
        if not d:
            rows.append(f"<tr><td>{label}</td><td colspan=3 style='color:#b91c1c'>missing</td></tr>")
            continue
        change = d["change"]["text"] if d.get("change") else "–"
        updated = d["updated_at_iso"][:16].replace("T", " ")
        rows.append(
            f"<tr><td>{label}</td><td><b>{fmt(d)}</b></td><td>{change}</td>"
            f"<td>{html.escape(d['source'])}, updated {updated}</td></tr>"
        )
    return (
        "<table cellpadding=6 style='border-collapse:collapse;font-size:14px' border=1>"
        "<tr style='background:#f1f5f9'><th>Indicator</th><th>Value</th><th>vs yesterday</th><th>Source</th></tr>"
        + "".join(rows) + "</table>"
    )


def _send(subject: str, body_html: str, image: Optional[Path] = None, attachments: Optional[List[Path]] = None) -> None:
    to = settings.ALERT_RECIPIENT_EMAIL
    if not to:
        raise ValueError("ALERT_RECIPIENT_EMAIL is not set")
    attachments = [a for a in (attachments or []) if a and a.exists()]
    image = image if image and image.exists() else None

    if settings.EMAIL_SERVICE == "resend":
        import resend
        resend.api_key = settings.RESEND_API_KEY
        files = ([image] if image else []) + attachments
        if image:
            body_html = body_html.replace("cid:preview", "cid:preview-image")
        resend.Emails.send({
            "from": f"{FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
            "to": [to],
            "subject": subject,
            "html": body_html,
            "attachments": [
                {"filename": f.name, "content": base64.b64encode(f.read_bytes()).decode(),
                 **({"content_id": "preview-image"} if f == image else {})}
                for f in files
            ],
        })
        return

    if not (settings.GMAIL_USER and settings.GMAIL_APP_PASSWORD):
        raise ValueError("GMAIL_USER / GMAIL_APP_PASSWORD are not set")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{settings.GMAIL_USER}>"
    msg["To"] = to
    msg.set_content("This email needs an HTML-capable mail app.")
    if image:
        cid = make_msgid(domain="hassan-daily")
        msg.add_alternative(body_html.replace("cid:preview", f"cid:{cid[1:-1]}"), subtype="html")
        msg.get_payload()[1].add_related(image.read_bytes(), "image", "png", cid=cid)
        attachments = [image] + attachments  # also attach so it can be saved
    else:
        msg.add_alternative(body_html, subtype="html")
    for f in attachments:
        maintype, subtype = ("image", "png") if f.suffix == ".png" else ("text", "plain")
        msg.add_attachment(f.read_bytes(), maintype=maintype, subtype=subtype, filename=f.name)

    password = settings.GMAIL_APP_PASSWORD.replace(" ", "")
    if len(password) != 16:
        raise ValueError(f"GMAIL_APP_PASSWORD should be 16 letters (spaces don't count), found {len(password)}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(settings.GMAIL_USER, password)
        smtp.send_message(msg)


def _warning_box(warnings: List[str]) -> str:
    if not warnings:
        return ""
    items = "".join(f"<li>{html.escape(w)}</li>" for w in warnings)
    return f"<div style='background:#fef3c7;border:1px solid #f59e0b;padding:8px 12px;margin:0 0 14px'><b>Needs attention:</b><ul>{items}</ul></div>"


def send_preview(png: Path, caption: str, data: Dict[str, Any], status: str, warnings: Optional[List[str]] = None,
                 story: Optional[Path] = None) -> None:
    """Emails the finished image, the caption, and the numbers it was built from."""
    body = f"""
<div style="font-family:Arial,sans-serif;max-width:720px">
  <h2 style="margin:0 0 6px">HASSAN DAILY – {data['date']}</h2>
  <p style="margin:0 0 14px;color:#334155"><b>{html.escape(status)}</b></p>
  {_warning_box(warnings or [])}
  <img src="cid:preview" width="540" style="border:1px solid #e2e8f0;max-width:100%">
  {"<p style='color:#64748b'>The story version (1080×1920) is attached.</p>" if story else ""}
  <h3>Caption</h3>
  <div dir="rtl" style="white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;padding:12px;font-size:15px;line-height:1.6">{html.escape(caption)}</div>
  <h3>Numbers used</h3>
  {_price_rows(data)}
  <p style="color:#64748b;font-size:12px">All safety checks passed: prices present, recent, no abnormal jumps, and the image shows exactly these numbers.</p>
</div>"""
    _send(f"✅ HASSAN DAILY preview – {data['date']}", body, image=png, attachments=[story] if story else None)


def send_alert(reason: str, problems: List[str], data: Optional[Dict[str, Any]] = None,
               png: Optional[Path] = None) -> None:
    """Emails why the run stopped. Nothing is posted when this is sent."""
    items = "".join(f"<li>{html.escape(p)}</li>" for p in problems)
    body = f"""
<div style="font-family:Arial,sans-serif;max-width:720px">
  <h2 style="color:#b91c1c;margin:0 0 6px">Nothing was posted today</h2>
  <p><b>{html.escape(reason)}</b></p>
  <ul style="line-height:1.6">{items}</ul>
  {"<h3>Numbers fetched</h3>" + _price_rows(data) if data else ""}
  {'<h3>Image (not posted)</h3><img src="cid:preview" width="540" style="border:1px solid #e2e8f0;max-width:100%">' if png else ""}
  <p style="color:#64748b;font-size:12px">The run can be repeated once the problem is fixed. See the README section "When you get an alert email".</p>
</div>"""
    date = data["date"] if data else ""
    _send(f"⚠️ HASSAN DAILY: not posted {date} – {reason}", body, image=png)


def send_published(date: str, results: List[str], warnings: List[str], data: Dict[str, Any],
                   png: Optional[Path] = None, story: Optional[Path] = None, caption: str = "") -> None:
    """Confirms what was posted (or, in a dry run, what would have been), with the posted image."""
    items = "".join(f"<li>{html.escape(r)}</li>" for r in results)
    image = '<img src="cid:preview" width="540" style="border:1px solid #e2e8f0;max-width:100%">' if png else ""
    story_note = "<p style='color:#64748b'>The story image is attached.</p>" if story else ""
    caption_html = (f'<h3>Caption</h3><div dir="rtl" style="white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;'
                    f'padding:12px;font-size:15px;line-height:1.6">{html.escape(caption)}</div>') if caption else ""
    body = f"""
<div style="font-family:Arial,sans-serif;max-width:720px">
  <h2 style="color:#15803d;margin:0 0 6px">Posted – {date}</h2>
  {_warning_box(warnings)}
  <ul style="line-height:1.8">{items}</ul>
  {image}
  {story_note}
  {caption_html}
  <h3>Numbers used</h3>
  {_price_rows(data)}
</div>"""
    _send(f"📣 HASSAN DAILY posted – {date}", body, image=png, attachments=[story] if story else None)
