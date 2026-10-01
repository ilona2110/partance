"""Envoi de l'email d'alerte (Gmail ou tout serveur SMTP)."""
import html
import os
import smtplib
import ssl
from email.message import EmailMessage


def configured():
    return bool(os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS"))


def _fmt_eur(n):
    return f"{n:,}".replace(",", " ") + " €"


def build(items, site_url):
    """items : liste de (offre, score ou None, atouts, manques). Renvoie (sujet, texte, html)."""
    n = len(items)
    o0 = items[0][0]
    if n == 1:
        subject = f"Nouvelle offre VIE : {o0['titre']} ({o0['ent']}, {o0.get('ville') or o0.get('pays') or ''})".replace(", )", ")")
    else:
        subject = f"{n} nouvelles offres VIE pour toi, dont {o0['titre']} ({o0['ent']})"
    rows_txt, rows_html = [], []
    for o, s, ok, ko in items:
        lieu = ", ".join(x for x in [o.get("ville"), o.get("pays")] if x)
        meta = " · ".join(x for x in [
            lieu,
            f"{_fmt_eur(o['ind'])}/mois" if o.get("ind") else None,
            f"{o['duree']} mois" if o.get("duree") else None,
            o.get("source"),
        ] if x)
        sc = f"{s}/100" if s is not None else "score indisponible"
        why = []
        if ok:
            why.append("Atouts : " + ", ".join(ok[:4]))
        if ko:
            why.append("Manque : " + ", ".join(ko[:3]))
        rows_txt.append(f"- [{sc}] {o['titre']} | {o['ent']}\n  {meta}\n  {' | '.join(why)}\n  {o['url']}")
        color = "#1D7A4E" if (s or 0) >= 70 else "#9A5F00" if (s or 0) >= 50 else "#5E6278"
        rows_html.append(f"""
<tr><td style="padding:14px 0;border-bottom:1px solid #DCDCE6;vertical-align:top;width:58px">
  <div style="font:600 15px ui-monospace,Menlo,monospace;color:{color};border:2px solid {color};border-radius:50%;width:44px;height:44px;line-height:44px;text-align:center">{s if s is not None else '–'}</div>
</td><td style="padding:14px 0 14px 12px;border-bottom:1px solid #DCDCE6;vertical-align:top">
  <a href="{html.escape(o['url'])}" style="font:700 16px Arial,sans-serif;color:#8C1D40;text-decoration:none">{html.escape(o['titre'])}</a>
  <div style="font:14px Arial,sans-serif;color:#16192B;margin-top:2px">{html.escape(o['ent'])}</div>
  <div style="font:13px Arial,sans-serif;color:#5E6278;margin-top:2px">{html.escape(meta)}</div>
  <div style="font:13px Arial,sans-serif;color:#5E6278;margin-top:4px">{html.escape(' · '.join(why))}</div>
</td></tr>""")
    text = "\n\n".join(rows_txt) + f"\n\nToutes les offres : {site_url}\n"
    body = f"""<!doctype html><html><body style="margin:0;background:#F2F2F6;padding:20px">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:22px 24px;border:1px solid #DCDCE6">
<div style="font:800 20px Arial,sans-serif;color:#16192B">Partance</div>
<div style="font:14px Arial,sans-serif;color:#5E6278;margin:4px 0 6px">{n} nouvelle{'s' if n > 1 else ''} offre{'s' if n > 1 else ''} VIE qui te correspond{'ent' if n > 1 else ''}</div>
<table style="width:100%;border-collapse:collapse">{''.join(rows_html)}</table>
<p style="font:14px Arial,sans-serif;margin:18px 0 0"><a href="{html.escape(site_url)}" style="color:#8C1D40">Voir toutes les offres sur ton site</a></p>
</div></body></html>"""
    return subject, text, body


def send(items, site_url, prefix=""):
    user, pwd = os.environ["SMTP_USER"], os.environ["SMTP_PASS"].replace(" ", "")
    to = os.environ.get("EMAIL_TO") or user
    host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    port = int(os.environ.get("SMTP_PORT") or 465)
    subject, text, body = build(items, site_url)
    subject = prefix + subject
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Partance <{user}>"
    msg["To"] = to
    msg.set_content(text)
    msg.add_alternative(body, subtype="html")
    ctx = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
            s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls(context=ctx)
            s.login(user, pwd)
            s.send_message(msg)
    return subject
