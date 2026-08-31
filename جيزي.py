#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║  🤖 Abderahim net v7.3 — ملف واحد كامل                 ║
║  Djezzy Walk Rewards + MGM + Buy Offers + Admin          ║
║  مع دعم البروكسي (Proxy)                                ║
╚══════════════════════════════════════════════════════════╝
"""

import re
import os
import sys
import time
import random
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import telebot
from telebot import types

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️ الإعدادات الأساسية
# ══════════════════════════════════════════════════════════════════════════════

BOT_TOKEN     = os.getenv("BOT_TOKEN", "8596940781:AAEUEFHOkjdavcmDys7DfAnIexEHFJjTJIk")
ADMIN_ID      = int(os.getenv("ADMIN_ID", "7020515460"))
VERSION       = "7.3"
DB_PATH       = "abderahim_net.db"

# ── Proxy Settings ──────────────────────────────────────────────────────────
PROXY_URL = os.getenv("PROXY_URL", "http://change4.owlproxy.com:7778")
PROXY_USER = os.getenv("PROXY_USER", "0nwxY681eo70")
PROXY_PASS = os.getenv("PROXY_PASS", "custom_zone_DZ_st__city_sid_74705687_time_5")
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "true").lower() == "true"

# بناء البروكسي مع المصادقة
if PROXY_ENABLED and PROXY_USER and PROXY_PASS:
    # استخراج الـ host والـ port من PROXY_URL
    proxy_clean = PROXY_URL.replace("http://", "").replace("https://", "")
    PROXY_FULL = f"http://{PROXY_USER}:{PROXY_PASS}@{proxy_clean}"
    PROXIES = {
        "http": PROXY_FULL,
        "https": PROXY_FULL
    }
else:
    PROXIES = None

# ── Djezzy API ────────────────────────────────────────────────────────────────
BASE_URL      = "https://apim.djezzy.dz/mobile-api"
TOKEN_URL     = f"{BASE_URL}/oauth2/token"
OTP_URL       = f"{BASE_URL}/oauth2/registration"
CLIENT_ID     = "87pIExRhxBb3_wGsA5eSEfyATloa"
CLIENT_SECRET = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
USER_AGENT    = "Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)"
USER_AGENT_V2 = "MobileApp/3.0.0"

# ── أكواد الباقات المجانية ─────────────────────────────────────────────────
PKG_1GO  = "GIFTWALKWIN1GO"
PKG_2GO  = "GIFTWALKWIN2GO"
PKG_4GO  = "GIFTWALKWIN4GO"

MAX_INVITES      = 5
MAX_OTP_ATTEMPTS = 3

STATE_UNKNOWN = 0
STATE_READY   = 1
STATE_WAITING = 2
_UNSET_HISTORY = object()   # sentinel: يميّز "لم يُمرَّر history" عن "history=None فعلياً"

# ── قائمة عروض الشراء ────────────────────────────────────────────────────────
OFFERS = {
    "DOVINTSPEEDDAY100MoPRE":    {"name": "📦 300Mo  ──  30 دج  ──  24 ساعة",       "display": "300Mo  |  30 دج  |  24 ساعة"},
    "DOVINTSPEEDDAY250MoPRE":    {"name": "📦 600Mo  ──  50 دج  ──  24 ساعة",       "display": "600Mo  |  50 دج  |  24 ساعة"},
    "DOVINTSPEEDDAY1GoPRE":      {"name": "📦 2Go  ──  100 دج  ──  24 ساعة",        "display": "2Go  |  100 دج  |  24 ساعة"},
    "OFFREJEUNE50":              {"name": "📦 1Go  ──  50 دج  ──  24 ساعة",         "display": "1Go  |  50 دج  |  24 ساعة"},
    "BTLINTSPEEDDAY2Go":         {"name": "🏷️ 4GB  ──  70 دج  ──  24 ساعة",        "display": "4GB  |  70 دج  |  24 ساعة"},
    "BTL500MBDAY":               {"name": "📦 3GB  ──  90 دج  ──  24 ساعة",         "display": "3GB  |  90 دج  |  24 ساعة"},
    "BTL4GBDAY":                 {"name": "📦 5GB  ──  190 دج  ──  24 ساعة",        "display": "5GB  |  190 دج  |  24 ساعة"},
    "BTL1GBDAY":                 {"name": "📦 4GB  ──  140 دج  ──  24 ساعة",        "display": "4GB  |  140 دج  |  24 ساعة"},
    "DOVINTSPEEDWEEK2GoPRE":     {"name": "📦 4Go  ──  150 دج  ──  7 أيام",         "display": "4Go  |  150 دج  |  7 أيام"},
    "DOVINTSPEEDWEEK3GoPRE":     {"name": "📦 10Go  ──  300 دج  ──  7 أيام",        "display": "10Go  |  300 دج  |  7 أيام"},
    "BTLDATA2WEEKS":             {"name": "📦 4GB  ──  400 دج  ──  15 يوم",         "display": "4GB  |  400 دج  |  15 يوم"},
    "1GBFB3DAYInternet":         {"name": "📦 1GB فيسبوك  ──  70 دج  ──  3 أيام",   "display": "1GB فيسبوك  |  70 دج  |  3 أيام"},
    "DOVINTSPEEDMONTH6GoPRE":    {"name": "📦 12Go  ──  500 دج  ──  30 يوم",        "display": "12Go  |  500 دج  |  30 يوم"},
    "DOVINTSPEEDMONTH15GoPRE":   {"name": "📦 30Go  ──  1000 دج  ──  30 يوم",       "display": "30Go  |  1000 دج  |  30 يوم"},
    "DOVINTSPEEDMONTH30GoPRE":   {"name": "📦 60Go  ──  1500 دج  ──  30 يوم",       "display": "60Go  |  1500 دج  |  30 يوم"},
    "2GBMONTH":                  {"name": "📦 3GB  ──  250 دج  ──  30 يوم",         "display": "3GB  |  250 دج  |  30 يوم"},
    "BTL500MBHOUR":              {"name": "⚡ 1GB  ──  40 دج  ──  1 ساعة",          "display": "1GB  |  40 دج  |  ساعة"},
    "ImtiyazSurpriseData2hfbPRE":{"name": "📘 فيسبوك غير محدود  ──  50 دج  ──  4 ساعات", "display": "فيسبوك غير محدود  |  50 دج  |  4 ساعات"},
}

OFFERS_DAILY   = ["DOVINTSPEEDDAY100MoPRE","DOVINTSPEEDDAY250MoPRE","DOVINTSPEEDDAY1GoPRE",
                   "OFFREJEUNE50","BTLINTSPEEDDAY2Go","BTL500MBDAY","BTL4GBDAY","BTL1GBDAY","BTL500MBHOUR"]
OFFERS_WEEKLY  = ["DOVINTSPEEDWEEK2GoPRE","DOVINTSPEEDWEEK3GoPRE","BTLDATA2WEEKS","1GBFB3DAYInternet"]
OFFERS_MONTHLY = ["DOVINTSPEEDMONTH6GoPRE","DOVINTSPEEDMONTH15GoPRE","DOVINTSPEEDMONTH30GoPRE","2GBMONTH"]
OFFERS_SPECIAL = ["ImtiyazSurpriseData2hfbPRE"]

# ══════════════════════════════════════════════════════════════════════════════
# 📝 Logging
# ══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("AbderahimNetBot")

# ══════════════════════════════════════════════════════════════════════════════
# 🗄️ قاعدة البيانات SQLite
# ══════════════════════════════════════════════════════════════════════════════

sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("timestamp", lambda b: datetime.fromisoformat(b.decode()))


def init_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT, username TEXT, phone TEXT,
        registered_at TIMESTAMP, last_active TIMESTAMP, banned INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
        user_id INTEGER PRIMARY KEY, access_token TEXT,
        refresh_token TEXT, expires_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, phone TEXT,
        offer_type TEXT, activated_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        invited_phone TEXT, invited_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS otp_attempts (
        phone TEXT PRIMARY KEY, attempts INTEGER DEFAULT 0, last_attempt TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scheduled (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, phone TEXT,
        offer_type TEXT, remind_at TIMESTAMP, sent INTEGER DEFAULT 0)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN username TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()
    logger.info("✅ قاعدة البيانات جاهزة")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ── Users ─────────────────────────────────────────────────────────────────────

def db_add_user(uid, name="", username="", phone=None):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users "
            "(user_id,name,username,phone,registered_at,last_active,banned) "
            "VALUES(?,?,?,?,?,?,COALESCE((SELECT banned FROM users WHERE user_id=?),0))",
            (uid, name, username, phone, datetime.now(), datetime.now(), uid))

def db_get_user(uid):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def db_get_phone(uid):
    with get_db() as conn:
        r = conn.execute("SELECT phone FROM users WHERE user_id=?", (uid,)).fetchone()
        return r["phone"] if r else None

def db_update_phone(uid, phone):
    with get_db() as conn:
        conn.execute("UPDATE users SET phone=? WHERE user_id=?", (phone, uid))

def db_update_name(uid, name):
    with get_db() as conn:
        conn.execute("UPDATE users SET name=? WHERE user_id=?", (name, uid))

def db_update_username(uid, username):
    with get_db() as conn:
        conn.execute("UPDATE users SET username=? WHERE user_id=?", (username, uid))

def db_is_banned(uid):
    with get_db() as conn:
        r = conn.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        return bool(r["banned"]) if r else False

def db_ban(uid):
    with get_db() as conn:
        conn.execute("UPDATE users SET banned=1 WHERE user_id=?", (uid,))

def db_unban(uid):
    with get_db() as conn:
        conn.execute("UPDATE users SET banned=0 WHERE user_id=?", (uid,))

def db_all_users():
    with get_db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM users")]

def db_user_count():
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

# ── Tokens ────────────────────────────────────────────────────────────────────

def db_save_tokens(uid, access, refresh=None, expires_in=3600):
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO tokens VALUES(?,?,?,?)",
                     (uid, access, refresh, datetime.now() + timedelta(seconds=expires_in)))

def db_get_token_row(uid):
    with get_db() as conn:
        return conn.execute(
            "SELECT access_token,refresh_token,expires_at FROM tokens WHERE user_id=?",
            (uid,)).fetchone()

def db_clear_tokens(uid):
    with get_db() as conn:
        conn.execute("DELETE FROM tokens WHERE user_id=?", (uid,))

def db_clear_all_tokens():
    with get_db() as conn:
        conn.execute("DELETE FROM tokens")

# ── OTP ───────────────────────────────────────────────────────────────────────

def db_otp_attempts(phone):
    with get_db() as conn:
        r = conn.execute("SELECT attempts FROM otp_attempts WHERE phone=?", (phone,)).fetchone()
        return r["attempts"] if r else 0

def db_inc_otp(phone):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO otp_attempts(phone,attempts,last_attempt) VALUES(?,1,?) "
            "ON CONFLICT(phone) DO UPDATE SET attempts=attempts+1,last_attempt=excluded.last_attempt",
            (phone, datetime.now()))

def db_reset_otp(phone):
    with get_db() as conn:
        conn.execute("DELETE FROM otp_attempts WHERE phone=?", (phone,))

# ── Activations ───────────────────────────────────────────────────────────────

def db_save_activation(uid, phone, offer):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO activations(user_id,phone,offer_type,activated_at) VALUES(?,?,?,?)",
            (uid, phone, offer, datetime.now()))

def db_last_activation(phone, offer):
    with get_db() as conn:
        return conn.execute(
            "SELECT activated_at FROM activations WHERE phone=? AND offer_type=? "
            "ORDER BY activated_at DESC LIMIT 1", (phone, offer)).fetchone()

def db_total_activations():
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM activations").fetchone()[0]

# ── Invitations ───────────────────────────────────────────────────────────────

def db_invite_count(uid):
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM invitations WHERE user_id=?", (uid,)).fetchone()[0]

def db_add_invitation(uid, phone):
    with get_db() as conn:
        if conn.execute("SELECT id FROM invitations WHERE user_id=? AND invited_phone=?",
                        (uid, phone)).fetchone():
            return False, "⚠️ هذا الرقم تمت دعوته مسبقاً"
        count = conn.execute("SELECT COUNT(*) FROM invitations WHERE user_id=?", (uid,)).fetchone()[0]
        if count >= MAX_INVITES:
            return False, f"⚠️ وصلت للحد الأقصى ({MAX_INVITES} دعوات)"
        conn.execute("INSERT INTO invitations(user_id,invited_phone,invited_at) VALUES(?,?,?)",
                     (uid, phone, datetime.now()))
        return True, f"✓ تم الإرسال ({count+1}/{MAX_INVITES})"

def db_invite_list(uid):
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT invited_phone,invited_at FROM invitations WHERE user_id=? ORDER BY invited_at DESC",
            (uid,))]

# ── Reminders ─────────────────────────────────────────────────────────────────

def db_schedule_reminder(uid, phone, offer, seconds):
    with get_db() as conn:
        conn.execute("DELETE FROM scheduled WHERE user_id=? AND phone=? AND offer_type=? AND sent=0",
                     (uid, phone, offer))
        conn.execute("INSERT INTO scheduled(user_id,phone,offer_type,remind_at) VALUES(?,?,?,?)",
                     (uid, phone, offer, datetime.now() + timedelta(seconds=seconds)))

def db_due_reminders():
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id,user_id,offer_type FROM scheduled WHERE remind_at<=? AND sent=0",
            (datetime.now(),)).fetchall()]

def db_mark_reminder_sent(rid):
    with get_db() as conn:
        conn.execute("UPDATE scheduled SET sent=1 WHERE id=?", (rid,))

# ══════════════════════════════════════════════════════════════════════════════
# 🛠️ دوال مساعدة
# ══════════════════════════════════════════════════════════════════════════════

def format_phone(p):
    d = re.sub(r"\D", "", str(p))
    if not d: return ""
    if d.startswith("213"): d = d[3:]
    if len(d) == 9: d = "0" + d
    if d.startswith("0") and len(d) == 10: return "213" + d[1:]
    return "213" + d

def mask_phone(p):
    d = re.sub(r"\D", "", str(p))
    if len(d) >= 12: return d[:3] + "●●●●" + d[-3:]
    if len(d) >= 10: return d[:2] + "●●●●●" + d[-2:]
    return "07●●●●●"

def fmt_time(ms):
    if ms <= 0: return "جاهز ✓"
    s = ms // 1000
    d, h, m = s // 86400, (s % 86400) // 3600, (s % 3600) // 60
    if d: return f"{d}ي {h}س"
    if h: return f"{h}س {m}د"
    return f"{m}د"

def fmt_seconds(sec):
    if sec <= 0: return "0 ثانية"
    d, h, m, s = sec//86400, (sec%86400)//3600, (sec%3600)//60, sec%60
    parts = []
    if d: parts.append(f"{d} يوم")
    if h: parts.append(f"{h} ساعة")
    if m: parts.append(f"{m} دقيقة")
    if s and not d and not h: parts.append(f"{s} ثانية")
    return " و".join(parts)

def is_valid_dz_number(raw):
    return bool(re.match(r"^07\d{8}$", re.sub(r"\D","",raw)))

def get_offer_state(phone, offer):
    row = db_last_activation(phone, offer)
    if not row: return STATE_UNKNOWN, 0
    elapsed = datetime.now() - row["activated_at"]
    cooldown = timedelta(days=1) if offer in ("1g","daily") else timedelta(days=7)
    if elapsed >= cooldown: return STATE_READY, 0
    return STATE_WAITING, int((cooldown - elapsed).total_seconds() * 1000)

def get_offer_state_real(uid, phone, offer, history=_UNSET_HISTORY):
    """
    نفس get_offer_state لكن تتحقق فعلياً من Djezzy (سجل الاشتراك الحقيقي)
    بدل الاعتماد فقط على سجل بوتنا المحلي — الذي قد يكون فارغاً أو قديماً
    إن فعّل المستخدم العرض من التطبيق الرسمي مباشرة أو أعيد ضبط قاعدة
    البيانات. يُرجع (state, remaining_ms, confirmed) حيث confirmed=True يعني
    الحالة مؤكدة من Djezzy فعلياً، وFalse تعني أنها تقدير من سجلنا المحلي فقط
    (بسبب تعذر الاتصال بجيزي في هذه اللحظة).
    """
    pkg_code = PKG_1GO if offer == "1g" else PKG_2GO
    cooldown_s = 86400 if offer == "1g" else 7*24*3600
    if history is _UNSET_HISTORY:
        history = api_subscription_history(uid, phone)
    if history is not None:
        last_ts = _last_walk_win_date_typed(history, pkg_code)
        if not last_ts:
            return STATE_READY, 0, True
        elapsed = time.time() - last_ts
        if elapsed >= cooldown_s:
            return STATE_READY, 0, True
        return STATE_WAITING, int((cooldown_s - elapsed) * 1000), True
    # تعذر التحقق الحقيقي (خطأ شبكة/توكن) → نرجع لتقدير محلي مع وسم "غير مؤكد"
    st, rem = get_offer_state(phone, offer)
    return st, rem, False

# ══════════════════════════════════════════════════════════════════════════════
# 🌐 HTTP Session مع دعم البروكسي
# ══════════════════════════════════════════════════════════════════════════════

def _make_session():
    s = requests.Session()
    r = Retry(total=3, backoff_factor=0.5,
              status_forcelist=[500,502,503,504],
              allowed_methods=["GET","POST"])
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.mount("http://",  HTTPAdapter(max_retries=r))
    
    # ── إعداد البروكسي إذا كان مفعلاً ──────────────────────────────────────
    if PROXY_ENABLED and PROXIES:
        s.proxies.update(PROXIES)
        logger.info(f"🌐 Proxy enabled: {PROXY_URL}")
        
        # إضافة headers إضافية لتحسين التوافق مع البروكسي
        s.headers.update({
            "Proxy-Connection": "keep-alive",
        })
    
    return s

_session = _make_session()
_BASE_H = {"User-Agent": USER_AGENT, "Accept": "application/json", "accept-language": "ar"}

def _log_api(url, status, note=""):
    icon = "✓" if status in (200,201,204) else "✗"
    logger.info(f"🌐 [{icon}] {note or url.split('/')[-1]} ({status})")

def _extract_djezzy_error(resp):
    """
    يسحب الرسالة الحقيقية من ردّ API جيزي (JSON) بغض النظر عن هيكل الردّ،
    بدل عرض رسائل عامة غير دقيقة للمستخدم عند فشل التفعيل.
    """
    if resp is None:
        return None
    try:
        body = resp.json()
    except Exception:
        return None
    if not isinstance(body, dict):
        return None
    errors = body.get("errors")
    if isinstance(errors, list) and errors:
        e0 = errors[0]
        if isinstance(e0, dict):
            detail = e0.get("detail") or e0.get("title") or e0.get("message") or ""
            if detail:
                return str(detail)
    _data = body.get("data")
    msg = body.get("message") or (_data.get("message") if isinstance(_data, dict) else None)
    if isinstance(msg, dict):
        ar = msg.get("ar", "")
        en = msg.get("en", "")
        return ar or en or None
    if isinstance(msg, str) and msg:
        return msg
    ed = body.get("errorDescription")
    if isinstance(ed, str) and ed:
        return ed
    fault = body.get("fault", {})
    if isinstance(fault, dict):
        fs = fault.get("faultstring", "")
        if fs:
            return str(fs)
    return None

# ══════════════════════════════════════════════════════════════════════════════
# 🔑 Token Management
# ══════════════════════════════════════════════════════════════════════════════

_EARLY_REFRESH_BUFFER = timedelta(seconds=90)

def _refresh_access_token(uid, refresh_tok, max_attempts=2):
    """
    يجدد توكن Djezzy عبر refresh_token. يعيد المحاولة عند أخطاء الشبكة/429
    العابرة (لا رفض حقيقي من الخادم) بدل الاستسلام من أول محاولة فاشلة —
    هذا هو السبب الرئيسي وراء فقدان تسجيل الدخول أحياناً أثناء نظام الدعوات
    رغم أن الـ refresh_token ما زال صالحاً فعلياً.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            resp = _session.post(TOKEN_URL,
                headers={**_BASE_H, "Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type":"refresh_token","refresh_token":refresh_tok,
                      "client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,"scope":"openid"},
                timeout=12)
            _log_api(TOKEN_URL, resp.status_code, "🔄 RefreshToken")
            if resp.status_code == 200:
                data = resp.json()
                db_save_tokens(uid, data["access_token"], data.get("refresh_token", refresh_tok),
                               data.get("expires_in", 3600))
                return f"Bearer {data['access_token']}"
            if resp.status_code == 429:
                time.sleep(0.7)
                continue
            if resp.status_code in (400, 401):
                logger.warning(f"refresh_token: refresh_token مرفوض (HTTP {resp.status_code})")
                return None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logger.warning(f"refresh_token #{attempt}: خطأ شبكة عابر — {e}")
            time.sleep(0.5)
            continue
        except Exception as e:
            logger.error(f"refresh_token error: {e}")
            return None
    return None

def get_token(uid):
    """
    يعيد توكن Djezzy صالحاً للاستخدام. يجدد التوكن مبكراً (قبل 90 ثانية من
    انتهائه فعلياً) بدل الانتظار حتى اللحظة الأخيرة، لتفادي سباق التوقيت الذي
    يجعل الطلب يصل للخادم بعد انتهاء الصلاحية فيفشل بلا داعٍ — وهو السبب
    الرئيسي في فقدان الجلسة أثناء نظام الدعوات.
    """
    row = db_get_token_row(uid)
    if not row: return None
    exp = row["expires_at"]
    if isinstance(exp, str):
        try: exp = datetime.fromisoformat(exp)
        except Exception: exp = None
    if exp and exp - _EARLY_REFRESH_BUFFER > datetime.now():
        return f"Bearer {row['access_token']}"
    if row["refresh_token"]:
        new_tok = _refresh_access_token(uid, row["refresh_token"])
        if new_tok:
            return new_tok
        if exp and exp > datetime.now():
            return f"Bearer {row['access_token']}"
        return None
    return None

# ══════════════════════════════════════════════════════════════════════════════
# 📱 OTP API
# ══════════════════════════════════════════════════════════════════════════════

def _jitter(base):
    """تأخير مع تشويش عشوائي لتفريق موجات الطلبات المتزامنة بدل أن تصطدم
    كلها بـ Djezzy في نفس اللحظة."""
    return base + random.uniform(0, base * 0.6)

# ── تهدئة إرسال OTP ───────────────────────────────────────────────────────
# تضمن فارقاً زمنياً أدنى (+ تشويش عشوائي) بين كل إرسال OTP فعلي والذي
# يليه، مهما كان عدد المستخدمين الذين يطلبون الرمز في نفس اللحظة. هذا يمنع
# وصول عشرات طلبات OTP خلال ثوانٍ قليلة من نفس الـ IP، وهو سبب شائع لحظر/
# تقييد الـ IP عند مزوّدي SMS الحسّاسين لمعدّل الطلبات.
_otp_throttle_lock = threading.Lock()
_last_otp_send_ts = [0.0]
OTP_SEND_MIN_GAP = float(os.getenv("OTP_SEND_MIN_GAP", "3"))  # ثوانٍ بين كل إرسال OTP والتالي له

def _throttle_otp_send():
    with _otp_throttle_lock:
        now = time.time()
        wait = (_last_otp_send_ts[0] + OTP_SEND_MIN_GAP) - now
        if wait > 0:
            time.sleep(wait + random.uniform(0, 1.0))
        _last_otp_send_ts[0] = time.time()

# ── تهدئة التحقق من OTP ───────────────────────────────────────────────────
# فارق أقصر من فارق الإرسال (الرمز صالح لدقائق قليلة فقط، فلا نُبطئ تجربة
# المستخدم)، لكنه كافٍ لمنع اصطدام عدة تحققات متزامنة بـ Djezzy في نفس
# اللحظة من نفس الـ IP.
_otp_verify_throttle_lock = threading.Lock()
_last_otp_verify_ts = [0.0]
OTP_VERIFY_MIN_GAP = float(os.getenv("OTP_VERIFY_MIN_GAP", "1.5"))  # ثوانٍ بين كل تحقق فعلي والتالي له

def _throttle_otp_verify():
    with _otp_verify_throttle_lock:
        now = time.time()
        wait = (_last_otp_verify_ts[0] + OTP_VERIFY_MIN_GAP) - now
        if wait > 0:
            time.sleep(wait + random.uniform(0, 0.5))
        _last_otp_verify_ts[0] = time.time()

def api_request_otp(msisdn, max_attempts=4):
    if db_otp_attempts(msisdn) >= MAX_OTP_ATTEMPTS:
        return False, "🔒 تجاوزت الحد الأقصى (3 محاولات). انتظر 30 دقيقة."
    for attempt in range(1, max_attempts + 1):
        try:
            _throttle_otp_send()
            resp = _session.post(OTP_URL,
                headers={**_BASE_H, "Content-Type": "application/json"},
                json={"consent-agreement":[{"marketing-notifications":False}],"is-consent":True},
                params={"msisdn":msisdn,"client_id":CLIENT_ID,"scope":"smsotp"},
                timeout=15)
            _log_api(OTP_URL, resp.status_code, f"📨 OTP → {msisdn[:6]}...")
            if resp.status_code in (200,201):
                db_inc_otp(msisdn)
                return True, "✓"
            elif resp.status_code == 400:
                return False, "❌ الرقم غير مسجل في Djezzy"
            elif resp.status_code == 429:
                if attempt < max_attempts:
                    time.sleep(_jitter(1.2))
                    continue
                return False, "❌ محاولات كثيرة، أعد المحاولة بعد قليل"
            else:
                if attempt < max_attempts:
                    time.sleep(_jitter(0.4))
                    continue
                return False, f"❌ خطأ {resp.status_code}"
        except Exception as e:
            logger.error(f"request_otp #{attempt}: {e}")
            if attempt < max_attempts:
                time.sleep(_jitter(0.4))
                continue
            return False, "❌ خطأ في الاتصال"
    return False, "❌ تعذر إرسال الرمز، حاول مرة أخرى"

def api_verify_otp(msisdn, otp, uid, max_attempts=10, _bad_code_retries=1):
    bad_code_seen = 0
    for attempt in range(1, max_attempts + 1):
        try:
            _throttle_otp_verify()
            resp = _session.post(TOKEN_URL,
                headers={**_BASE_H, "Content-Type": "application/x-www-form-urlencoded"},
                data={"otp":otp,"mobileNumber":msisdn,"scope":"djezzyAppV2",
                      "client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,"grant_type":"mobile"},
                timeout=15)
            _log_api(TOKEN_URL, resp.status_code, "🔐 VerifyOTP")
            if resp.status_code == 200:
                data = resp.json()
                db_save_tokens(uid, data["access_token"], data.get("refresh_token"), data.get("expires_in",3600))
                db_reset_otp(msisdn)
                return True, data.get("firstName") or data.get("displayName") or "", "✓"
            elif resp.status_code == 400:
                if bad_code_seen < _bad_code_retries and attempt < max_attempts:
                    bad_code_seen += 1
                    time.sleep(_jitter(0.4))
                    continue
                return False, None, "❌ الرمز غير صحيح"
            elif resp.status_code == 429:
                if attempt < max_attempts:
                    time.sleep(_jitter(min(0.7 * attempt, 4.0)))
                    continue
                return False, None, "❌ محاولات كثيرة، أعد المحاولة بعد قليل"
            else:
                if attempt < max_attempts:
                    time.sleep(_jitter(0.3))
                    continue
                return False, None, f"❌ خطأ {resp.status_code}"
        except Exception as e:
            logger.error(f"verify_otp #{attempt}: {e}")
            if attempt < max_attempts:
                time.sleep(_jitter(0.3))
                continue
            return False, None, "❌ خطأ في الاتصال"
    return False, None, "❌ فشل التحقق، حاول مرة أخرى"

# ══════════════════════════════════════════════════════════════════════════════
# 💰 Balance API
# ══════════════════════════════════════════════════════════════════════════════

def api_get_balance(uid, phone):
    token = get_token(uid)
    if not token: return None, "❌ سجل دخول"
    headers = {**_BASE_H, "Authorization": token}
    for url in [f"{BASE_URL}/api/v1/subscribers/main-balance/{phone}",
                f"{BASE_URL}/api/v1/account/summary"]:
        try:
            resp = _session.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                bal = (data.get("balance",{}).get("mainBalance")
                    or data.get("balance",{}).get("availableBalance")
                    or data.get("data",{}).get("mainBalance"))
                if bal is not None: return str(bal), None
        except Exception as e:
            logger.warning(f"balance error: {e}")
    return None, "⚠️ تعذر الجلب"

# ══════════════════════════════════════════════════════════════════════════════
# 👤 معلومات الحساب الكاملة (اسم الباقة الرسمي، نوع الشريحة، الباقات النشطة...)
# ══════════════════════════════════════════════════════════════════════════════

def api_get_full_account_info(uid, phone):
    """
    يجلب معلومات الحساب الكاملة من Djezzy عبر رابط main-balance الغني بالـ
    includes، ويرجع dict يحوي الرصيد ونوع الشريحة الرسمي (offer_name) بدل
    Prepaid/Postpaid العام، والباقات النشطة حالياً.
    """
    token = get_token(uid)
    if not token:
        return None
    url = (
        f"{BASE_URL}/api/v1/subscribers/main-balance/{phone}"
        "?include=surprise-products,subscription-type-illegibility,connected-products,"
        "subscription-history,flash-products,supplementary-informations,available-services"
    )
    headers = {**_BASE_H, "Authorization": token, "Connection": "Keep-Alive"}
    for attempt in range(3):
        try:
            resp = _session.get(url, headers=headers, timeout=15)
            if resp.status_code == 401 and attempt < 2:
                row = db_get_token_row(uid)
                if row and row["refresh_token"]:
                    new_tok = _refresh_access_token(uid, row["refresh_token"])
                    if new_tok:
                        headers["Authorization"] = new_tok
                continue
            if resp.status_code != 200:
                break
            raw  = resp.json()
            data = raw.get("data", {}) or {}
            info = data.get("customerInformations", {}) or {}

            pt_raw = (info.get("paymentType") or "").strip()
            if pt_raw.upper() == "PREPAID":
                payment_type = "Prepaid 💳"
            elif pt_raw.upper() == "POSTPAID":
                payment_type = "Postpaid 📄"
            else:
                payment_type = pt_raw or "—"

            sub_type = info.get("subscriptionType", {})
            sim_type_code = ""
            offer_name = "—"
            if isinstance(sub_type, dict):
                names = sub_type.get("name", {})
                sim_type_code = str(sub_type.get("code", "") or "").strip()
                if isinstance(names, dict):
                    offer_name = names.get("ar") or names.get("en") or sim_type_code or "—"
                else:
                    offer_name = sim_type_code or "—"

            connected = data.get("connectedProducts") or data.get("connected-products") or []
            connected_names = []
            if isinstance(connected, list):
                for cp in connected[:5]:
                    if isinstance(cp, dict):
                        n = cp.get("name") or cp.get("description") or cp.get("code", "")
                        if isinstance(n, dict):
                            n = n.get("ar") or n.get("en") or ""
                        if n:
                            connected_names.append(str(n))

            _bal_raw = data.get("mainBalance")
            real_sim_name = offer_name
            if offer_name and offer_name != "—" and sim_type_code and sim_type_code.upper() not in offer_name.upper():
                real_sim_name = f"{offer_name} ({sim_type_code})"
            elif offer_name == "—" and sim_type_code:
                real_sim_name = sim_type_code

            return {
                "balance":            str(_bal_raw) if _bal_raw is not None else None,
                "payment_type":       payment_type,
                "offer_name":         offer_name,
                "sim_type_code":      sim_type_code,
                "real_sim_name":      real_sim_name,
                "connected_products": connected_names,
                "activation_date":    (info.get("activationTime") or "")[:10] or "—",
            }
        except Exception as e:
            logger.warning(f"api_get_full_account_info #{attempt+1}: {e}")
        time.sleep(0.3)
    return None

# ══════════════════════════════════════════════════════════════════════════════
# 📜 Subscription History API
# ══════════════════════════════════════════════════════════════════════════════

def api_subscription_history(uid, phone):
    token = get_token(uid)
    if not token: return None
    try:
        resp = _session.get(
            f"{BASE_URL}/api/v1/subscribers/subscription-history/{phone}",
            headers={**_BASE_H, "Authorization": token, "accept-language":"fr"},
            timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data,dict) and data.get("status") == 200:
                return data.get("data",[])
            return data if isinstance(data,list) else None
    except Exception as e:
        logger.warning(f"subscription_history: {e}")
    return None

def _last_walk_win_date(history):
    for item in (history or []):
        code = item.get("packageCode","")
        if code in ("GIFTWALKWIN2GO","GIFTWALKWIN1GO","GIFTWALKWIN4GO"):
            dt_str = item.get("subscriptionDateTime")
            if dt_str:
                try:
                    from dateutil import parser as dp
                    return int(dp.parse(dt_str).timestamp())
                except Exception:
                    try:
                        return int(datetime.fromisoformat(dt_str[:19]).timestamp())
                    except Exception:
                        pass
    return None

def _last_walk_win_date_typed(history, pkg_code):
    """
    مثل _last_walk_win_date لكن لباقة واحدة محددة فقط. مهم لأن 1GB (تبريد
    24 ساعة) و2GB (تبريد 7 أيام) لهما كودان مختلفان — الجمع بينهما في تاريخ
    واحد (كما كان سابقاً) قد يجعل تفعيل إحداهما يُحسب خطأً كتبريد للأخرى.
    """
    for item in (history or []):
        if item.get("packageCode","") == pkg_code:
            dt_str = item.get("subscriptionDateTime")
            if dt_str:
                try:
                    from dateutil import parser as dp
                    return int(dp.parse(dt_str).timestamp())
                except Exception:
                    try:
                        return int(datetime.fromisoformat(dt_str[:19]).timestamp())
                    except Exception:
                        pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
# 🎁 Walk Reward API (مجاني)
# ══════════════════════════════════════════════════════════════════════════════

# Djezzy يرفض تفعيل الهدايا المجانية (Walk 1GB/2GB) لأي رقم لا يملك باقة
# مدفوعة نشطة — هذا شرط حقيقي من الخادم (HTTP 402/403)، وبعض إصدارات الـ API
# تُعيده أيضاً كـ 400/404/422 مع رسالة نصية بدل كود واضح. نتحقق من كل الأشكال
# هنا بدل عرض رسالة عامة/تقنية تُحيّر المستخدم بلا فائدة.
_NEED_PAID_PKG_HINTS = (
    "غير مؤهل", "not eligible", "eligibility not found", "eligib",
    "تعذر معالجة", "لا وجود للمكافأة", "no active", "باقة",
)

def api_activate_walk(uid, phone, pkg_code, max_attempts=5, timeout=15):
    """
    يفعّل عرض Walk المجاني، ويصنّف سبب الفشل الحقيقي بدل عرض رسالة عامة:
      - "NEED_100DZ"      → الرقم يحتاج باقة مدفوعة (≥100دج) نشطة أولاً (شرط حقيقي من Djezzy)
      - نص واضح آخر       → رسالة Djezzy الفعلية عند توفرها
      - "❌ فشل التفعيل..." → فشل عام بعد استنفاد كل المحاولات
    يجرب كلا إصداري API (v1/v2) في كل محاولة، ويعيد المحاولة بسرعة عند 429
    أو عند الحاجة لتجديد التوكن (fault 900901) بدل الاستسلام من أول عائق عابر.
    """
    token = get_token(uid)
    if not token: return False, "❌ سجل دخول"
    headers = {**_BASE_H, "Content-Type":"application/json",
               "Authorization":token, "User-Agent":USER_AGENT_V2}
    urls = [f"{BASE_URL}/api/v1/services/walk/activate-reward/{phone}",
            f"{BASE_URL}/api/v2/services/walk/activate-reward/{phone}"]
    last_msg = None
    for attempt in range(1, max_attempts+1):
        for url in urls:
            try:
                resp = _session.post(url, headers=headers, json={"packageCode":pkg_code}, timeout=timeout)
                _log_api(url, resp.status_code, f"🎁 Walk/{pkg_code} #{attempt}")
                if resp.status_code in (200,201,204): return True, "✓ تم التفعيل"
                if resp.status_code in (402, 403):
                    return False, "NEED_100DZ"
                if resp.status_code == 429:
                    time.sleep(0.7); continue
                try:
                    body = resp.json()
                except Exception:
                    body = {}
                fault = body.get("fault", {})
                if isinstance(fault, dict) and int(fault.get("code", 0)) == 900901:
                    row = db_get_token_row(uid)
                    if row and row["refresh_token"]:
                        new_tok = _refresh_access_token(uid, row["refresh_token"])
                        if new_tok: headers["Authorization"] = new_tok
                    continue
                if resp.status_code in (400, 404, 422):
                    real = _extract_djezzy_error(resp)
                    if real and any(h.lower() in real.lower() for h in _NEED_PAID_PKG_HINTS):
                        return False, "NEED_100DZ"
                    if real:
                        last_msg = real
            except Exception as e:
                logger.warning(f"walk_reward #{attempt}: {e}")
        if attempt < max_attempts:
            time.sleep(0.3)
    return False, (last_msg or "❌ فشل التفعيل — حاول لاحقاً")

# ══════════════════════════════════════════════════════════════════════════════
# 🛍️ Buy/Activate Product API (مدفوع)
# ══════════════════════════════════════════════════════════════════════════════

def api_activate_product(uid, phone, pkg_code, max_attempts=2, timeout=12):
    token = get_token(uid)
    if not token: return False, "❌ سجل دخول"
    url = f"{BASE_URL}/api/v1/subscribers/activate-product/{phone}"
    headers = {**_BASE_H, "Content-Type":"application/json",
               "Authorization":token, "User-Agent":USER_AGENT_V2, "accept-language":"fr"}
    for attempt in range(1, max_attempts+1):
        try:
            resp = _session.post(url, headers=headers, json={"packageCode":pkg_code}, timeout=timeout)
            _log_api(url, resp.status_code, f"🔖 Product/{pkg_code} #{attempt}")
            if resp.status_code in (200,201,204):
                try:
                    data = resp.json()
                    msg_raw = data.get("message","")
                    msg_str = msg_raw.get("en","") if isinstance(msg_raw,dict) else str(msg_raw)
                    if "successfully" in msg_str.lower() or resp.status_code == 201:
                        return True, "✓ تم التفعيل"
                    if resp.status_code == 200 and data.get("status") == 200:
                        return True, "✓ تم التفعيل"
                except Exception:
                    return True, "✓ تم التفعيل"
            if resp.status_code == 402:
                real = _extract_djezzy_error(resp)
                try:
                    bal_data = resp.json()
                    balance = (bal_data.get("data") or {}).get("mainBalance")
                    if balance is not None:
                        return False, (real or "💳 رصيدك غير كافٍ") + f"\nرصيدك الحالي: {balance} دج"
                except Exception:
                    pass
                return False, real or "💳 رصيدك غير كافٍ"
            if resp.status_code == 403:
                real = _extract_djezzy_error(resp)
                return False, real or "🚫 يلزمك الاشتراك في باقة 100دج أو أكثر"
            if resp.status_code in (400, 404, 422):
                real = _extract_djezzy_error(resp)
                if real: return False, real
            if resp.status_code == 429: time.sleep(0.7); continue
            try:
                data = resp.json()
                fault = data.get("fault",{})
                if isinstance(fault,dict) and int(fault.get("code",0)) == 900901:
                    row = db_get_token_row(uid)
                    if row and row["refresh_token"]:
                        new_tok = _refresh_access_token(uid, row["refresh_token"])
                        if new_tok: headers["Authorization"] = new_tok
                    continue
                real = _extract_djezzy_error(resp)
                if real: return False, real
            except Exception: pass
        except Exception as e:
            logger.warning(f"activate_product #{attempt}: {e}")
    return False, "❌ تعذر التفعيل — الشريحة قد لا تدعم هذا العرض"

# ══════════════════════════════════════════════════════════════════════════════
# 👥 MGM (دعوة) API
# ══════════════════════════════════════════════════════════════════════════════

def api_fetch_mgm_invitations(uid, phone):
    token = get_token(uid)
    if not token: return None
    try:
        resp = _session.get(
            f"{BASE_URL}/api/v1/services/mgm/invitations/{phone}",
            headers={**_BASE_H, "Authorization":token, "User-Agent":USER_AGENT_V2},
            timeout=15)
        _log_api("mgm/invitations", resp.status_code, "📋 MGM Invitations")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data,dict) and data.get("status") == 200:
                return data.get("data",{})
            return data
    except Exception as e:
        logger.warning(f"fetch_mgm_invitations: {e}")
    return None

def api_send_mgm_invitation(uid, sender, receiver):
    token = get_token(uid)
    if not token: return False, "❌ سجل دخول"
    url = f"{BASE_URL}/api/v1/services/mgm/send-invitation/{sender}"
    headers = {**_BASE_H, "Content-Type":"application/json",
               "Authorization":token, "User-Agent":USER_AGENT_V2}
    try:
        resp = _session.post(url, headers=headers, json={"msisdnReciever":receiver}, timeout=15)
        _log_api(url, resp.status_code, f"📤 MGM Invite → {receiver[:8]}...")
        if resp.status_code in (200,201): return True, "✓"
        if resp.status_code == 400:
            try:
                data = resp.json()
                msg = data.get("message",{})
                ar = msg.get("ar","") if isinstance(msg,dict) else str(msg)
                if "وصلت إلى الحد الأقصى" in ar: return False, "⚠️ وصلت للحد الأقصى (5 دعوات)"
                if "تمت دعوة هذا المستلم" in ar or "هذه العملية غير متوفرة" in ar:
                    return False, "⚠️ هذا الرقم سبق دعوته"
                if "العميل غير موجود" in ar: return False, "❌ الرقم غير موجود في Djezzy"
            except Exception: pass
            real = _extract_djezzy_error(resp)
            return False, real or "❌ خطأ في الإرسال"
        if resp.status_code == 403: return False, "⚠️ هذا الرقم سبق دعوته"
        real = _extract_djezzy_error(resp)
        return False, real or f"❌ خطأ {resp.status_code}"
    except Exception as e:
        logger.error(f"send_mgm_invitation: {e}")
        return False, "❌ خطأ في الاتصال"

def api_delete_pending_invitations(uid, phone, pending_ids):
    """
    محاولة حذف الدعوات المعلقة — يجرب عدة أساليب:
    1. POST مع {"invitationId": id}
    2. DELETE مع {"invitationId": id}
    3. POST مع {"msisdn": phone, "invitationId": id}
    يعيد (نجح_عدد, فشل_عدد)
    """
    token = get_token(uid)
    if not token or not pending_ids: return 0, 0
    base_url = f"{BASE_URL}/api/v1/services/mgm/delete-invitation/{phone}"
    headers_json = {**_BASE_H, "Content-Type":"application/json",
                    "Authorization":token, "User-Agent":USER_AGENT_V2}
    ok_count = 0
    fail_count = 0
    for inv_id in pending_ids:
        if inv_id is None: continue
        deleted = False
        attempts = [
            ("POST",  base_url, {"invitationId": inv_id}),
            ("POST",  base_url, {"invitationId": inv_id, "msisdn": phone}),
            ("DELETE",base_url, {"invitationId": inv_id}),
            ("POST",  f"{BASE_URL}/api/v1/services/mgm/invitations/{phone}/delete", {"invitationId": inv_id}),
        ]
        for method, url, body in attempts:
            try:
                if method == "DELETE":
                    resp = _session.delete(url, headers=headers_json, json=body, timeout=15)
                else:
                    resp = _session.post(url, headers=headers_json, json=body, timeout=15)
                _log_api(url, resp.status_code, f"🗑 Delete({method}) id={inv_id}")
                if resp.status_code in (200, 201, 204):
                    deleted = True; break
                if resp.status_code == 404:
                    deleted = True; break
            except Exception as e:
                logger.warning(f"delete_pending method={method} id={inv_id}: {e}")
        if deleted:
            ok_count += 1
        else:
            fail_count += 1
    return ok_count, fail_count

def api_activate_mgm_reward(uid, phone, pkg_code):
    """Returns: SUCCESS | ALREADY_CLAIMED | REWARD_NOT_EXIST | ERROR"""
    token = get_token(uid)
    if not token: return "ERROR"
    url = f"{BASE_URL}/api/v1/services/mgm/activate-reward/{phone}"
    headers = {**_BASE_H, "Content-Type":"application/json",
               "Authorization":token, "User-Agent":USER_AGENT_V2}
    for attempt in range(1, 6):
        try:
            resp = _session.post(url, headers=headers, json={"packageCode":pkg_code}, timeout=15)
            _log_api(url, resp.status_code, f"🎁 MGM Reward/{pkg_code}")
            if resp.status_code in (200,201):
                try:
                    data = resp.json()
                    msg = data.get("message","")
                    msg_str = msg.get("en","") if isinstance(msg,dict) else str(msg)
                    if "successfully" in msg_str.lower() or resp.status_code == 201:
                        return "SUCCESS"
                except Exception:
                    return "SUCCESS"
            if resp.status_code == 404:
                try:
                    data = resp.json()
                    msg = data.get("message","")
                    if isinstance(msg,str) and "Eligibility not found" in msg:
                        return "ALREADY_CLAIMED"
                    if isinstance(msg,dict) and "لا وجود للمكافأة" in msg.get("ar",""):
                        return "REWARD_NOT_EXIST"
                except Exception: pass
                return "ALREADY_CLAIMED"
            if resp.status_code == 400:
                try:
                    data = resp.json()
                    msg = data.get("message",{})
                    ar = msg.get("ar","") if isinstance(msg,dict) else str(msg)
                    if "تعذر معالجة طلبك" in ar: return "ALREADY_CLAIMED"
                except Exception: pass
        except Exception as e:
            logger.warning(f"activate_mgm_reward #{attempt}: {e}")
        time.sleep(0.3)
    return "ERROR"

def api_try_mgm_bonus(uid, phone):
    """محاولة سحب مكافأة معلقة: SUCCESS_1GO | SUCCESS_500MO | ALREADY_CLAIMED | REWARD_NOT_EXIST | ERROR"""
    r1 = api_activate_mgm_reward(uid, phone, "MGMBONUS1Go")
    if r1 == "SUCCESS":         return "SUCCESS_1GO"
    if r1 == "ALREADY_CLAIMED": return "ALREADY_CLAIMED"
    if r1 == "REWARD_NOT_EXIST":
        r2 = api_activate_mgm_reward(uid, phone, "MGMBONUS500Mo")
        if r2 == "SUCCESS":         return "SUCCESS_500MO"
        if r2 == "ALREADY_CLAIMED": return "ALREADY_CLAIMED"
        return "REWARD_NOT_EXIST"
    return "ERROR"

# ══════════════════════════════════════════════════════════════════════════════
# 🎨 رسائل وتصميم
# ══════════════════════════════════════════════════════════════════════════════

def msg_welcome(name):
    return f"""🔷 مرحباً بك {name}

معك <b>Abderahim net</b> — الإصدار v{VERSION}

📶 حزمة 1GB مجانية تتجدد يومياً
📶 حزمة 2GB مجانية تتجدد أسبوعياً
🎫 نظام إحالة: ادعُ واربح بيانات إضافية
🗂 أكثر من 18 عرضاً جاهزاً للشراء

لتفعيل حسابك أرسل رقم هاتفك المسجّل في Djezzy:
<code>07xxxxxxxx</code>"""

def msg_otp_sent(phone):
    return f"""📮 تم إرسال رمز التفعيل إلى <code>{phone}</code>

⏱ الرمز صالح لمدة دقيقتين
اكتب الرمز المكوّن من 4 إلى 6 خانات:"""

def msg_otp_fail(phone, reason):
    return f"""⛔ تعذّر إرسال الرمز إلى <code>{phone}</code>

السبب: {reason}
يمكنك إعادة المحاولة أو استخدام رقم آخر"""

def msg_login_success(name, phone, username):
    uname = f"@{username}" if username else "غير محدّد"
    return f"""🟢 تم الدخول إلى حسابك يا {name}

الحساب: {uname}
الرقم: <code>{phone}</code>
المشغّل: Djezzy 🇩🇿

اختر خدمة من القائمة أسفله"""

def msg_offer_confirm(offer_name, size, phone):
    icons = {"1GB":"📶","2GB":"🎁","4GB":"🎀"}
    icon = icons.get(size,"🎁")
    return f"""{icon} تأكيد طلب: <b>{offer_name}</b>

الرقم: <code>{phone}</code>
الحجم: {size}
القيمة: مجانية

هل تُتابع؟"""

def msg_offer_waiting(offer_name, remain):
    return f"""⏸ <b>{offer_name}</b> غير متاح الآن

الوقت المتبقي: <code>{remain}</code>
سنُعلمك فور توفّره"""

def msg_offer_success(offer_name, size, phone):
    return f"""✅ نجح تفعيل <b>{offer_name}</b>

الرقم: <code>{phone}</code>
الحجم: {size}
القيمة: 0 دج

شكراً لاستخدامك Abderahim net"""

def msg_offer_fail(offer_name, err):
    return f"""⛔ تعذّر تفعيل <b>{offer_name}</b>

السبب: {err}
جرّب عرضاً آخر أو أعد المحاولة لاحقاً"""

def msg_account(name, username, phone, status1, status2, invites, balance,
                 sim_name=None, connected_products=None):
    uname = f"@{username}" if username else "غير محدّد"
    sim_line = f"\nنوع الشريحة: {sim_name}" if sim_name else ""
    active_line = ""
    if connected_products:
        active_line = "\n" + "\n".join(f"— {p}" for p in connected_products[:5])
    return f"""🗂 بطاقة الحساب

الاسم: <b>{name}</b>
الحساب: {uname}
الرقم: <code>{phone}</code>
المشغّل: Djezzy 🇩🇿
الرصيد: <code>{balance}</code>{sim_line}

🎁 الحزم المجانية
— 1GB: {status1}
— 2GB: {status2}
— دعوات مُرسَلة: <code