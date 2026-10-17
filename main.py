"""
Mobil Bütçe ve Finans Koçu (Mobile Budget & Finance Coach)
Tek dosya Flet + SQLite Uygulaması
Flet 1.0+ (ft.Alignment / ft.Border / ft.Padding / ft.NavigationBarDestination / ft.Button) ve eski sürümlerle %100 uyumludur.
"""
import flet as ft
import sqlite3
import datetime
import calendar
import random

import os

# Veritabanı Dosyası (Android APK ve Masaüstü Tam Uyumlu)
_STORAGE_DIR = os.environ.get("FLET_APP_STORAGE_DATA") or os.environ.get("FLET_APP_STORAGE_TEMP") or "."
os.makedirs(_STORAGE_DIR, exist_ok=True)
DB_NAME = os.path.join(_STORAGE_DIR, "budget.db")

# --- FLET SÜRÜM UYUMLULUK KATMANI ---
class SafeIcons:
    def __getattr__(self, name: str):
        if hasattr(ft, "Icons"):
            icons_obj = getattr(ft, "Icons")
            try:
                val = getattr(icons_obj, name)
                if val is not None:
                    return val
            except (AttributeError, KeyError):
                pass
        if hasattr(ft, "icons"):
            icons_obj = getattr(ft, "icons")
            try:
                val = getattr(icons_obj, name)
                if val is not None:
                    return val
            except (AttributeError, KeyError):
                pass
        return name.lower()

Icons = SafeIcons()

class SafeAlignment:
    def __getattr__(self, name: str):
        if hasattr(ft, "Alignment"):
            align_cls = getattr(ft, "Alignment")
            upper_name = name.upper()
            if hasattr(align_cls, upper_name):
                return getattr(align_cls, upper_name)
        if hasattr(ft, "alignment"):
            mod = getattr(ft, "alignment")
            if hasattr(mod, name.lower()):
                return getattr(mod, name.lower())
        coords = {
            "top_left": (-1.0, -1.0),
            "top_center": (0.0, -1.0),
            "top_right": (1.0, -1.0),
            "center_left": (-1.0, 0.0),
            "center": (0.0, 0.0),
            "center_right": (1.0, 0.0),
            "bottom_left": (-1.0, 1.0),
            "bottom_center": (0.0, 1.0),
            "bottom_right": (1.0, 1.0),
        }
        x, y = coords.get(name.lower(), (0.0, 0.0))
        if hasattr(ft, "Alignment"):
            return ft.Alignment(x, y)
        return (x, y)

align = SafeAlignment()

class SafeBorder:
    def all(self, width=1, color="#334155"):
        if hasattr(ft, "Border") and hasattr(ft.Border, "all"):
            return ft.Border.all(width, color)
        elif hasattr(ft, "border") and hasattr(ft.border, "all"):
            return ft.border.all(width, color)
        return None

border = SafeBorder()

class SafePadding:
    def all(self, val):
        if hasattr(ft, "Padding") and hasattr(ft.Padding, "all"):
            return ft.Padding.all(val)
        elif hasattr(ft, "padding") and hasattr(ft.padding, "all"):
            return ft.padding.all(val)
        return val

    def symmetric(self, vertical=0, horizontal=0):
        if hasattr(ft, "Padding") and hasattr(ft.Padding, "symmetric"):
            return ft.Padding.symmetric(vertical=vertical, horizontal=horizontal)
        elif hasattr(ft, "padding") and hasattr(ft.padding, "symmetric"):
            return ft.padding.symmetric(vertical=vertical, horizontal=horizontal)
        return {"vertical": vertical, "horizontal": horizontal}

    def only(self, left=0, top=0, right=0, bottom=0):
        if hasattr(ft, "Padding") and hasattr(ft.Padding, "only"):
            return ft.Padding.only(left=left, top=top, right=right, bottom=bottom)
        elif hasattr(ft, "padding") and hasattr(ft.padding, "only"):
            return ft.padding.only(left=left, top=top, right=right, bottom=bottom)
        return {"left": left, "top": top, "right": right, "bottom": bottom}

pad = SafePadding()

def Button(text=None, **kwargs):
    """Flet 1.0 (ft.Button) ve Flet 0.x (ft.ElevatedButton) evrensel uyumluluk sarmalayıcısı"""
    if hasattr(ft, "ElevatedButton"):
        return ft.ElevatedButton(text, **kwargs)
    elif hasattr(ft, "Button"):
        if text is not None and "content" not in kwargs:
            kwargs["content"] = text
        return ft.Button(**kwargs)
    return ft.Text(text or "")

def TextButton(text=None, **kwargs):
    """Flet 1.0 ve Flet 0.x TextButton uyumluluk sarmalayıcısı"""
    if hasattr(ft, "TextButton"):
        if text is not None and "content" not in kwargs:
            kwargs["content"] = text
        return ft.TextButton(**kwargs)
    elif hasattr(ft, "Button"):
        if text is not None and "content" not in kwargs:
            kwargs["content"] = text
        return ft.Button(**kwargs)
    return ft.Text(text or "")

def Option(key, text=None):
    """Flet 1.0 (ft.DropdownOption) ve Flet 0.x (ft.dropdown.Option) uyumluluğu"""
    if text is None:
        text = str(key)
    if hasattr(ft, "DropdownOption"):
        return ft.DropdownOption(key=str(key), text=str(text))
    elif hasattr(ft, "dropdown") and hasattr(ft.dropdown, "Option"):
        return ft.dropdown.Option(str(key), str(text))
    return str(key)

def NavDestination(**kwargs):
    """Flet 1.0 (ft.NavigationBarDestination) ve Flet 0.x (ft.NavigationDestination) uyumluluğu"""
    if hasattr(ft, "NavigationBarDestination"):
        return ft.NavigationBarDestination(**kwargs)
    elif hasattr(ft, "NavigationDestination"):
        return ft.NavigationDestination(**kwargs)
    return None


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # 1. Hesaplar ve Kredi Kartları Tablosu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Nakit', 'Banka', 'Kredi Kartı'
        balance REAL NOT NULL DEFAULT 0.0,
        total_limit REAL NOT NULL DEFAULT 0.0,
        current_debt REAL NOT NULL DEFAULT 0.0, -- Taksitler dahil toplam kullanılan (bloke) limit
        period_debt REAL NOT NULL DEFAULT 0.0,  -- Sadece bu ay ödenecek dönem (ekstre) borcu
        color TEXT DEFAULT '#2563EB',
        icon TEXT DEFAULT 'account_balance_wallet'
    )
    """)

    # Mevcut veritabanı için otomatik kolon yükseltmesi (Migration)
    try:
        cur.execute("ALTER TABLE accounts ADD COLUMN total_limit REAL NOT NULL DEFAULT 0.0")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE accounts ADD COLUMN current_debt REAL NOT NULL DEFAULT 0.0")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE accounts ADD COLUMN period_debt REAL NOT NULL DEFAULT 0.0")
    except Exception:
        pass
    # Eski kredi kartlarında bakiye olarak girilmiş değerleri toplam limite aktar, bakiyeyi 0 yap
    cur.execute("""
    UPDATE accounts 
    SET total_limit = balance, current_debt = 0.0, period_debt = 0.0, balance = 0.0 
    WHERE type = 'Kredi Kartı' AND total_limit = 0.0 AND balance > 0.0
    """)
    
    # 2. İşlemler Tablosu (Taksit ve Ortak Harcama Destekli)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL, -- YYYY-MM-DD
        type TEXT NOT NULL, -- 'Gider', 'Gelir'
        total_installments INTEGER DEFAULT 1,
        installment_index INTEGER DEFAULT 1,
        parent_id INTEGER,
        is_shared INTEGER DEFAULT 0,
        shared_person_count INTEGER DEFAULT 1,
        my_share REAL DEFAULT 0.0,
        receivable_amount REAL DEFAULT 0.0,
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    )
    """)
    
    # 3. Abonelikler / Düzenli Giderler Tablosu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        billing_day INTEGER NOT NULL, -- Ayın kaçıncı günü (1-31)
        category TEXT NOT NULL,
        account_id INTEGER,
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    )
    """)
    
    # 4. Alacak / Verecek (Ortak Harcama Bölüşümü)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS receivables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        person_name TEXT NOT NULL,
        amount REAL NOT NULL,
        is_collected INTEGER DEFAULT 0,
        date TEXT NOT NULL
    )
    """)
    
    # 5. Birikim Hedefleri
    cur.execute("""
    CREATE TABLE IF NOT EXISTS savings_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_amount REAL NOT NULL DEFAULT 0.0,
        icon TEXT DEFAULT 'flag'
    )
    """)
    
    # 6. Uygulama Ayarları / Kurulum Durumu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # Varsayılan başlangıç verileri (yalnızca ilk kurulumda yüklenir)
    cur.execute("SELECT value FROM app_settings WHERE key = 'is_seeded'")
    seeded = cur.fetchone()
    if not seeded:
        cur.executemany("""
        INSERT INTO accounts (name, type, balance, total_limit, current_debt, color, icon) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            ("Cüzdan (Nakit)", "Nakit", 1450.00, 0.0, 0.0, "#10B981", "payments"),
            ("Garanti BBVA", "Banka", 18500.00, 0.0, 0.0, "#0284C7", "account_balance"),
            ("İş Bankası Maximum", "Kredi Kartı", 0.0, 30000.00, 1200.00, "#6366F1", "credit_card")
        ])
        
        cur.executemany("""
        INSERT INTO subscriptions (name, amount, billing_day, category, account_id) VALUES (?, ?, ?, ?, ?)
        """, [
            ("Netflix Premium", 229.99, 14, "Eğlence", 3),
            ("Spotify Aile", 99.00, 20, "Müzik", 3),
            ("Ev İnterneti", 380.00, 25, "Fatura", 2),
            ("Kira & Aidat", 12500.00, 1, "Konut", 2)
        ])
        
        cur.executemany("""
        INSERT INTO savings_goals (title, target_amount, current_amount, icon) VALUES (?, ?, ?, ?)
        """, [
            ("Yeni Laptop", 45000.00, 31500.00, "laptop_mac"),
            ("Yaz Tatili Fonu", 25000.00, 12500.00, "beach_access"),
            ("Acil Durum Fonu", 50000.00, 48000.00, "shield")
        ])
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        cur.executemany("""
        INSERT INTO transactions (account_id, title, amount, category, date, type, total_installments, installment_index, is_shared, my_share, receivable_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (1, "Süpermarket Alışverişi", 840.0, "Market", today, "Gider", 1, 1, 0, 840.0, 0.0),
            (2, "Aylık Maaş Ödemesi", 42500.0, "Maaş", today, "Gelir", 1, 1, 0, 42500.0, 0.0),
            (3, "Restoran Akşam Yemeği", 1200.0, "Yeme & İçme", today, "Gider", 1, 1, 1, 400.0, 800.0)
        ])
        
        cur.execute("""
        INSERT INTO receivables (title, person_name, amount, is_collected, date) VALUES (?, ?, ?, ?, ?)
        """, ("Restoran Akşam Yemeği Payı", "Ahmet & Burak (2 kişi)", 800.0, 0, today))
        
        cur.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('is_seeded', '1')")
        
    conn.commit()
    conn.close()

init_db()

# Türkçe Takvim Sabitleri ve Tarih Yardımcıları
TURKISH_MONTHS = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]
TURKISH_DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TURKISH_DAYS_SHORT = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

def format_turkish_date(d: datetime.date, include_day_name=True):
    month_name = TURKISH_MONTHS[d.month]
    if include_day_name:
        day_name = TURKISH_DAYS[d.weekday()]
        return f"{d.day} {month_name} {d.year}, {day_name}"
    return f"{d.day} {month_name} {d.year}"

# Formatlayıcı Fonksiyonlar
def format_tl(val):
    return f"{val:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_active_date() -> datetime.date:
    """Sistem takvimini veya kullanıcının takvimden kalibre ettiği tarihi döndürür."""
    sys_today = datetime.date.today()
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT value FROM app_settings WHERE key = 'date_offset_days'")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            offset = int(row[0])
            return sys_today + datetime.timedelta(days=offset)
    except Exception:
        pass
    return sys_today

def set_active_date(target_date: datetime.date):
    """Kullanıcı takvimden bugünün tarihini kalibre ettiğinde farkı kaydeder."""
    sys_today = datetime.date.today()
    offset = (target_date - sys_today).days
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('date_offset_days', ?)", (str(offset),))
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "FinansKoç • Akıllı Mobil Finans Asistanı"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    
    # Pencere Boyutlandırma
    try:
        page.window.width = 440
        page.window.height = 840
        page.window.resizable = True
    except Exception:
        page.window_width = 440
        page.window_height = 840
        page.window_resizable = True

    # Renk Paleti
    PRIMARY = "#4F46E5"
    ACCENT = "#10B981"
    CARD_BG = "#1E293B"
    TEXT_MUTED = "#94A3B8"
    DANGER = "#EF4444"
    WARNING = "#F59E0B"

    current_tab_index = 0

    # Evrensel Dialog Açma / Kapatma (Tek tıkla kapanma garantili Flet 1.0 & 0.x uyumlu)
    def show_popup(dialog_control):
        if hasattr(page, "_dialogs") and hasattr(page._dialogs, "controls"):
            try:
                if dialog_control in page._dialogs.controls:
                    page._dialogs.controls.remove(dialog_control)
            except Exception:
                pass
        dialog_control.open = False
        if hasattr(page, "show_dialog"):
            try:
                page.show_dialog(dialog_control)
                return
            except Exception:
                pass
        if hasattr(page, "open"):
            try:
                page.open(dialog_control)
                return
            except Exception:
                pass
        page.dialog = dialog_control
        dialog_control.open = True
        page.update()

    def close_popup(dialog_control=None):
        if dialog_control is not None:
            dialog_control.open = False
            try:
                dialog_control.update()
            except Exception:
                pass
            if hasattr(page, "_dialogs") and hasattr(page._dialogs, "controls"):
                try:
                    if dialog_control in page._dialogs.controls:
                        page._dialogs.controls.remove(dialog_control)
                    page._dialogs.update()
                except Exception:
                    pass
            if hasattr(page, "close"):
                try:
                    page.close(dialog_control)
                except Exception:
                    pass
        elif hasattr(page, "pop_dialog"):
            try:
                page.pop_dialog()
            except Exception:
                pass
        page.update()

    # Bildirim (SnackBar)
    def notify(msg, color="#10B981"):
        sb = ft.SnackBar(
            content=ft.Text(msg, color="white", weight=ft.FontWeight.W_500),
            bgcolor=color,
            duration=2500
        )
        if hasattr(page, "show_dialog"):
            try:
                page.show_dialog(sb)
            except Exception:
                page.snack_bar = sb
                sb.open = True
                page.update()
        elif hasattr(page, "open"):
            try:
                page.open(sb)
            except Exception:
                page.snack_bar = sb
                sb.open = True
                page.update()
        else:
            page.snack_bar = sb
            sb.open = True
            page.update()

    # --- HESAPLAMA MOTORU (Finans Koçu & Takvim Entegreli Günlük Limit) ---
    def calculate_coach_metrics():
        conn = get_db()
        cur = conn.cursor()
        
        # Kredi kartı limitleri nakit para / gelir DEĞİLDİR! Sadece Nakit ve Banka bakiyeleri toplanır.
        cur.execute("SELECT SUM(balance) FROM accounts WHERE type IN ('Nakit', 'Banka')")
        liquid_assets = cur.fetchone()[0] or 0.0

        # Kredi kartı toplam limit ve güncel borç analizi
        cur.execute("SELECT SUM(total_limit), SUM(current_debt) FROM accounts WHERE type = 'Kredi Kartı'")
        cc_row = cur.fetchone()
        total_cc_limit = (cc_row[0] or 0.0) if cc_row else 0.0
        total_cc_debt = (cc_row[1] or 0.0) if cc_row else 0.0
        
        today = get_active_date()
        _, num_days = calendar.monthrange(today.year, today.month)
        # Ay sonuna kalan gün sayısı (Örn: 31 çeken Ekim ayının 18'inde: 31 - 18 = 13 gün kaldı)
        remaining_days = max(0, num_days - today.day)
        calc_days = max(1, remaining_days)
        month_name = TURKISH_MONTHS[today.month]
        
        cur.execute("SELECT SUM(amount) FROM subscriptions WHERE billing_day >= ?", (today.day,))
        upcoming_subs = cur.fetchone()[0] or 0.0
        
        cur.execute("""
        SELECT SUM(amount) FROM transactions 
        WHERE strftime('%Y-%m', date) = ? AND type = 'Gider'
        """, (today.strftime("%Y-%m"),))
        month_spent = cur.fetchone()[0] or 0.0

        safe_budget = max(0.0, liquid_assets - upcoming_subs)
        daily_safe_limit = safe_budget / calc_days

        cur.execute("""
        SELECT category, SUM(amount) as cat_total 
        FROM transactions 
        WHERE type = 'Gider' AND strftime('%Y-%m', date) = ? 
        GROUP BY category ORDER BY cat_total DESC
        """, (today.strftime("%Y-%m"),))
        cat_stats = cur.fetchall()

        advice_list = []
        if cat_stats:
            top_cat = cat_stats[0]
            if top_cat["cat_total"] > (month_spent * 0.35) and month_spent > 0:
                advice_list.append(f"💡 En büyük giderin '{top_cat['category']}' ({format_tl(top_cat['cat_total'])}). Bu alanda %15 kısarak ayda {format_tl(top_cat['cat_total']*0.15)} tasarruf edebilirsin!")
        
        if total_cc_limit > 0 and (total_cc_debt / total_cc_limit) > 0.40:
            utilization_pct = int((total_cc_debt / total_cc_limit) * 100)
            advice_list.append(f"💳 Kredi kartı limit kullanım oranın %{utilization_pct} ({format_tl(total_cc_debt)} bloke). Kredi notunu korumak için bu oranı %30-40 altında tutman önerilir.")

        if upcoming_subs > 0:
            advice_list.append(f"📅 {month_name} ayı sonuna kadar {format_tl(upcoming_subs)} tutarında sabit ödemen var, bütçeni buna göre koru.")
        
        if daily_safe_limit > 500:
            advice_list.append(f"🎯 Harika gidiyorsun! Günlük bütçen gayet rahat ({format_tl(daily_safe_limit)}/gün). Fazlasını hedefine aktarabilirsin.")
        else:
            advice_list.append(f"⚠️ Dikkat: Kalan {remaining_days} gün için bütçen kısıtlı ({format_tl(daily_safe_limit)}/gün). Acil olmayan harcamaları ertelemeni öneririm.")

        conn.close()
        return {
            "liquid_assets": liquid_assets,
            "total_cc_limit": total_cc_limit,
            "total_cc_debt": total_cc_debt,
            "daily_safe_limit": daily_safe_limit,
            "remaining_days": remaining_days,
            "num_days": num_days,
            "today": today,
            "month_name": month_name,
            "upcoming_subs": upcoming_subs,
            "month_spent": month_spent,
            "advice": advice_list
        }

    # ==========================================
    # MODAL DİYALOGLARI
    # ==========================================
    
    # 1. YENİ HARCAMA / GELİR EKLE DIALOGU (TAKVİM SEÇİCİ DESTEKLİ)
    selected_trans_date = {"date": get_active_date()}
    input_title = ft.TextField(label="Açıklama / Başlık", prefix_icon=Icons.EDIT, border_radius=10)
    input_amount = ft.TextField(label="Tutar (₺)", prefix_icon=Icons.ATTACH_MONEY, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    input_category = ft.Dropdown(
        label="Kategori",
        options=[
            Option("Market"),
            Option("Yeme & İçme"),
            Option("Ulaşım / Akaryakıt"),
            Option("Alışveriş & Giyim"),
            Option("Faturalar & Abonelik"),
            Option("Eğlence"),
            Option("Maaş / Gelir"),
            Option("Diğer"),
        ],
        value="Market",
        border_radius=10
    )
    input_type = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="Gider", label="Gider"),
            ft.Radio(value="Gelir", label="Gelir"),
        ]),
        value="Gider"
    )
    input_account = ft.Dropdown(label="Hesap / Kart", border_radius=10)
    
    input_installments = ft.Dropdown(
        label="Taksit Sayısı",
        options=[
            Option("1", "Tek Çekim (Peşin)"),
            Option("2", "2 Taksit"),
            Option("3", "3 Taksit"),
            Option("4", "4 Taksit"),
            Option("6", "6 Taksit"),
            Option("9", "9 Taksit"),
            Option("12", "12 Taksit"),
        ],
        value="1",
        border_radius=10
    )

    trans_date_label = ft.Text(f"📅 İşlem Tarihi: {format_turkish_date(selected_trans_date['date'], False)}", size=12.5, color="white", weight=ft.FontWeight.W_500)

    def on_trans_date_picked(e):
        if trans_date_picker.value:
            picked = trans_date_picker.value
            if isinstance(picked, datetime.datetime):
                picked = picked.date()
            selected_trans_date["date"] = picked
            trans_date_label.value = f"📅 İşlem Tarihi: {format_turkish_date(picked, False)}"
            page.update()

    trans_date_picker = ft.DatePicker(
        first_date=datetime.date(2023, 1, 1),
        last_date=datetime.date(2030, 12, 31),
        help_text="İşlem Tarihini Seçin",
        cancel_text="İptal",
        confirm_text="Seç",
        on_change=on_trans_date_picked
    )

    def open_trans_date_picker(e=None):
        trans_date_picker.value = selected_trans_date["date"]
        show_popup(trans_date_picker)

    trans_date_row = ft.Container(
        content=ft.Row([
            trans_date_label,
            TextButton("Takvimden Seç", on_click=open_trans_date_picker)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=pad.symmetric(horizontal=12, vertical=4),
        border_radius=10,
        bgcolor="#0F172A",
        border=border.all(1, "#334155")
    )
    
    is_shared_check = ft.Checkbox(value=False)
    input_split_persons = ft.TextField(label="Toplam Kişi Sayısı", value="2", keyboard_type=ft.KeyboardType.NUMBER, visible=False, border_radius=10)
    input_other_person_name = ft.TextField(label="Alacaklı Kişi/Grup Adı", value="Arkadaşlar", visible=False, border_radius=10)

    def on_shared_toggle(e=None):
        input_split_persons.visible = bool(is_shared_check.value)
        input_other_person_name.visible = bool(is_shared_check.value)
        page.update()

    is_shared_check.on_change = on_shared_toggle

    shared_toggle_row = ft.Container(
        content=ft.Row([
            is_shared_check,
            ft.Text("Ortak Harcama (Hesabı Arkadaşlarla Bölüş)", size=12.5, color="white", expand=True)
        ], spacing=8),
        on_click=lambda e: (setattr(is_shared_check, "value", not is_shared_check.value), on_shared_toggle())
    )

    # FİŞ TARAMA (OCR Benzetimi)
    ocr_progress = ft.ProgressBar(visible=False, color=ACCENT)
    ocr_status_text = ft.Text("", size=12, color=TEXT_MUTED, italic=True)

    def simulate_ocr_scan(e=None):
        ocr_progress.visible = True
        ocr_status_text.value = "AI OCR Modeli fiş görselini analiz ediyor..."
        page.update()
        
        mock_receipts = [
            {"title": "Migros Sanal Market", "amount": 648.50, "cat": "Market"},
            {"title": "Shell Akaryakıt", "amount": 1250.00, "cat": "Ulaşım / Akaryakıt"},
            {"title": "Starbucks Coffee", "amount": 195.00, "cat": "Yeme & İçme"},
            {"title": "Teknosa Mağazacılık", "amount": 3499.00, "cat": "Alışveriş & Giyim"},
            {"title": "Getir Yemek Siparişi", "amount": 385.00, "cat": "Yeme & İçme"},
        ]
        choice = random.choice(mock_receipts)
        
        input_title.value = choice["title"]
        input_amount.value = str(choice["amount"])
        input_category.value = choice["cat"]
        input_type.value = "Gider"
        
        ocr_progress.visible = False
        ocr_status_text.value = f"✅ Fiş başarıyla okundu: {choice['title']} ({format_tl(choice['amount'])})"
        page.update()
        notify(f"Fiş Tarandı: {choice['title']} tutarı çekildi! 🧾", ACCENT)

    ocr_picker_btn = Button(
        "📷 Fiş Görseli Tara (Akıllı OCR)",
        icon=Icons.DOCUMENT_SCANNER,
        bgcolor="#334155",
        color="white",
        on_click=simulate_ocr_scan
    )

    def refresh_account_dropdown():
        selected_trans_date["date"] = get_active_date()
        trans_date_label.value = f"📅 İşlem Tarihi: {format_turkish_date(selected_trans_date['date'], False)}"
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, type, balance, total_limit, current_debt FROM accounts")
        accs = cur.fetchall()
        opts = []
        for a in accs:
            if a["type"] == "Kredi Kartı":
                avail_lim = max(0.0, (a["total_limit"] or 0.0) - (a["current_debt"] or 0.0))
                opts.append(Option(str(a["id"]), f"💳 {a['name']} (Kullanılabilir Limit: {format_tl(avail_lim)})"))
            else:
                opts.append(Option(str(a["id"]), f"🏦 {a['name']} (Bakiye: {format_tl(a['balance'])})"))
        input_account.options = opts
        if accs:
            input_account.value = str(accs[0]["id"])
        conn.close()

    def save_transaction_submit(e):
        try:
            total_amt = float(input_amount.value.replace(",", "."))
            if total_amt <= 0:
                notify("Geçerli bir tutar giriniz!", DANGER)
                return
        except Exception:
            notify("Lütfen sayısal bir tutar giriniz!", DANGER)
            return

        if not input_title.value.strip():
            notify("Lütfen bir açıklama giriniz!", DANGER)
            return

        if not input_account.value:
            notify("Lütfen önce bir Banka veya Kredi Kartı tanımlayın!", WARNING)
            return

        acc_id = int(input_account.value)
        trans_type = input_type.value
        cat = input_category.value
        title = input_title.value.strip()
        installments = int(input_installments.value)
        is_shared = 1 if is_shared_check.value else 0
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE id = ?", (acc_id,))
        acc = cur.fetchone()
        if not acc:
            conn.close()
            notify("Seçilen hesap bulunamadı!", DANGER)
            return

        is_credit_card = (acc["type"] == "Kredi Kartı")

        # Kredi kartına doğrudan gelir eklenemez (Limit nakit para değildir)
        if is_credit_card and trans_type == "Gelir":
            conn.close()
            notify("Kredi kartına gelir eklenemez! Kart borcu ödemek için kart üzerindeki 'Borç Öde' butonunu kullanın.", WARNING)
            return

        # Kredi kartı kullanılabilir limit kontrolü
        if is_credit_card and trans_type == "Gider":
            avail_limit = max(0.0, (acc["total_limit"] or 0.0) - (acc["current_debt"] or 0.0))
            if (acc["total_limit"] or 0.0) > 0 and total_amt > avail_limit:
                conn.close()
                notify(f"Kart kullanılabilir limiti yetersiz! (Kullanılabilir Limit: {format_tl(avail_limit)})", DANGER)
                return

        today = selected_trans_date["date"]
        
        my_share = total_amt
        receivable = 0.0
        if is_shared:
            try:
                persons = max(2, int(input_split_persons.value))
            except Exception:
                persons = 2
            my_share = round(total_amt / persons, 2)
            receivable = round(total_amt - my_share, 2)
            other_name = input_other_person_name.value.strip() or "Arkadaşlar"
            
            cur.execute("""
            INSERT INTO receivables (title, person_name, amount, is_collected, date)
            VALUES (?, ?, ?, ?, ?)
            """, (f"{title} (Pay)", other_name, receivable, 0, today.strftime("%Y-%m-%d")))

        toast_msg = ""
        if installments > 1 and trans_type == "Gider":
            monthly_amt = round(total_amt / installments, 2)
            cur.execute("""
            INSERT INTO transactions (account_id, title, amount, category, date, type, total_installments, installment_index, is_shared, my_share, receivable_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (acc_id, f"{title} (1/{installments})", monthly_amt, cat, today.strftime("%Y-%m-%d"), trans_type, installments, 1, is_shared, my_share, receivable))
            parent_id = cur.lastrowid
            
            curr_y, curr_m = today.year, today.month
            for i in range(2, installments + 1):
                curr_m += 1
                if curr_m > 12:
                    curr_m = 1
                    curr_y += 1
                future_date = datetime.date(curr_y, curr_m, min(today.day, 28)).strftime("%Y-%m-%d")
                cur.execute("""
                INSERT INTO transactions (account_id, title, amount, category, date, type, total_installments, installment_index, parent_id, is_shared, my_share, receivable_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (acc_id, f"{title} ({i}/{installments})", monthly_amt, cat, future_date, trans_type, installments, i, parent_id, 0, 0.0, 0.0))
            
            if is_credit_card:
                # Kredi kartında taksitli alışveriş toplam tutar kadar kullanılabilir limiti bloke eder,
                # ancak BU AY ÖDENECEK DÖNEM BORCUNA sadece ilk taksit (monthly_amt) yansır!
                cur.execute(
                    "UPDATE accounts SET current_debt = current_debt + ?, period_debt = period_debt + ? WHERE id = ?",
                    (total_amt, monthly_amt, acc_id)
                )
                toast_msg = f"{installments} Taksit planlandı! Bu ay ödenecek: +{format_tl(monthly_amt)} (Toplam Bloke: {format_tl(total_amt)}) 💳"
            else:
                cur.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (monthly_amt, acc_id))
                toast_msg = f"{installments} Taksit planlandı! İlk taksit ({format_tl(monthly_amt)}) yansıtıldı. 💳"
        else:
            cur.execute("""
            INSERT INTO transactions (account_id, title, amount, category, date, type, total_installments, installment_index, is_shared, my_share, receivable_amount)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?)
            """, (acc_id, title, total_amt, cat, today.strftime("%Y-%m-%d"), trans_type, is_shared, my_share, receivable))
            
            if is_credit_card:
                cur.execute(
                    "UPDATE accounts SET current_debt = current_debt + ?, period_debt = period_debt + ? WHERE id = ?",
                    (total_amt, total_amt, acc_id)
                )
                toast_msg = f"Tek çekim harcama kaydedildi! Bu ay ödenecek borç +{format_tl(total_amt)} arttı. 💳"
            else:
                if trans_type == "Gider":
                    cur.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (total_amt, acc_id))
                else:
                    cur.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (total_amt, acc_id))
                toast_msg = f"İşlem kaydedildi! ({format_tl(total_amt)}) ✅"

        conn.commit()
        conn.close()
        
        input_title.value = ""
        input_amount.value = ""
        is_shared_check.value = False
        input_split_persons.visible = False
        input_other_person_name.visible = False
        input_installments.value = "1"
        ocr_status_text.value = ""
        # ÖNCE DİYALOĞU KAPAT, SONRA BİLDİRİM GÖSTER (Tek tıkla kapanması için)
        close_popup(add_transaction_dialog)
        render_current_view()
        if toast_msg:
            notify(toast_msg, ACCENT)
        page.update()

    add_transaction_dialog = ft.AlertDialog(
        title=ft.Text("Yeni İşlem Ekle", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                ocr_picker_btn,
                ocr_progress,
                ocr_status_text,
                ft.Divider(color="#334155"),
                input_type,
                trans_date_row,
                input_title,
                input_amount,
                input_category,
                input_account,
                input_installments,
                shared_toggle_row,
                input_split_persons,
                input_other_person_name,
            ], scroll=ft.ScrollMode.AUTO, spacing=10),
            width=360,
            height=480,
        ),
        actions=[
            TextButton("İptal", on_click=lambda e: close_popup(add_transaction_dialog)),
            Button("Kaydet", bgcolor=PRIMARY, color="white", on_click=save_transaction_submit),
        ]
    )

    # 2. YENİ HESAP VEYA KREDİ KARTI EKLE DİYALOGU (TOPLAM LİMİT, KULLANILABİLİR LİMİT & TAKSİTLİ DÖNEM BORCU AYRIMLI)
    new_acc_name = ft.TextField(label="Hesap / Kart Adı (örn: Ziraat, Bonus Kart)", border_radius=10)
    new_acc_type = ft.Dropdown(
        label="Hesap Türü",
        options=[
            Option("Banka", "Banka Hesabı (Vadesiz)"),
            Option("Nakit", "Nakit Cüzdan"),
            Option("Kredi Kartı", "Kredi Kartı (Toplam & Kullanılabilir Limit)"),
        ],
        value="Banka",
        border_radius=10
    )
    new_acc_balance = ft.TextField(label="Mevcut Bakiye (₺)", value="0", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, visible=True)
    new_acc_limit = ft.TextField(label="Toplam Kart Limiti (₺)", value="50000", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, visible=False)
    new_acc_avail_limit = ft.TextField(label="Kullanılabilir Limit (₺)", value="50000", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, visible=False)
    new_acc_debt_installments = ft.Dropdown(
        label="Kullanılan Limit (Fark) Kaç Taksit?",
        options=[
            Option("0", "Manuel (Bu Ay Ödenecek Tutarı Kendim Gireceğim)"),
            Option("1", "Tek Çekim (Tamamı Bu Ay Ödenecek)"),
            Option("2", "2 Taksit (Aylık Eşit Böl)"),
            Option("3", "3 Taksit (Aylık Eşit Böl)"),
            Option("4", "4 Taksit (Aylık Eşit Böl)"),
            Option("6", "6 Taksit (Aylık Eşit Böl)"),
            Option("9", "9 Taksit (Aylık Eşit Böl)"),
            Option("12", "12 Taksit (Aylık Eşit Böl)"),
        ],
        value="3",
        border_radius=10,
        visible=False
    )
    new_acc_period_debt = ft.TextField(
        label="Bu Ay Ödenecek Dönem Borcu / Ekstre (₺)",
        value="0",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        visible=False
    )
    cc_debt_preview = ft.Text(
        "",
        size=11.5,
        color=WARNING,
        weight=ft.FontWeight.BOLD,
        visible=False
    )
    cc_info_note = ft.Text(
        "ℹ️ Toplam Limit ile Kullanılabilir Limit arasındaki fark taksitli bloke olarak tutulur; tamamını bu ay ödemezsiniz.",
        size=11,
        color=ACCENT,
        visible=False
    )

    def recalculate_new_cc_period_debt(from_plan_change=True):
        try:
            t_lim = float((new_acc_limit.value or "0").replace(",", "."))
            a_lim = float((new_acc_avail_limit.value or "0").replace(",", "."))
            total_blocked = max(0.0, t_lim - a_lim)
            plan_inst = int(new_acc_debt_installments.value or "0")
            if from_plan_change and plan_inst > 0:
                monthly_pay = round(total_blocked / plan_inst, 2)
                new_acc_period_debt.value = str(monthly_pay)
            p_debt = min(total_blocked, max(0.0, float((new_acc_period_debt.value or "0").replace(",", "."))))
            future_block = max(0.0, total_blocked - p_debt)
            cc_debt_preview.value = (
                f"📌 Toplam Limit Blokesi: {format_tl(total_blocked)}\n"
                f"💳 Bu Ay Ödenecek: {format_tl(p_debt)} | ⏳ İleri Taksitler: {format_tl(future_block)}"
            )
        except Exception:
            cc_debt_preview.value = "📌 Toplam Limit Blokesi: 0,00 ₺"
        page.update()

    new_acc_limit.on_change = lambda e: recalculate_new_cc_period_debt(True)
    new_acc_avail_limit.on_change = lambda e: recalculate_new_cc_period_debt(True)
    new_acc_debt_installments.on_change = lambda e: recalculate_new_cc_period_debt(True)
    new_acc_period_debt.on_change = lambda e: (setattr(new_acc_debt_installments, "value", "0"), recalculate_new_cc_period_debt(False))

    def on_acc_type_change(e=None):
        is_cc = (new_acc_type.value == "Kredi Kartı")
        new_acc_balance.visible = not is_cc
        new_acc_limit.visible = is_cc
        new_acc_avail_limit.visible = is_cc
        new_acc_debt_installments.visible = is_cc
        new_acc_period_debt.visible = is_cc
        cc_debt_preview.visible = is_cc
        cc_info_note.visible = is_cc
        recalculate_new_cc_period_debt(True)

    new_acc_type.on_change = on_acc_type_change

    def open_add_account_modal(default_type="Banka"):
        new_acc_type.value = default_type
        on_acc_type_change()
        show_popup(add_account_dialog)

    def save_new_account(e):
        name = new_acc_name.value.strip()
        if not name:
            notify("Lütfen hesap veya kart adı yazın!", DANGER)
            return
        
        acc_t = new_acc_type.value
        conn = get_db()
        cur = conn.cursor()

        if acc_t == "Kredi Kartı":
            try:
                lim = float(new_acc_limit.value.replace(",", "."))
                if lim <= 0:
                    conn.close()
                    notify("Kredi kartı toplam limiti 0'dan büyük olmalıdır!", DANGER)
                    return
            except Exception:
                conn.close()
                notify("Geçerli bir toplam kart limiti giriniz!", DANGER)
                return
            try:
                avail_lim = float(new_acc_avail_limit.value.replace(",", "."))
                if avail_lim < 0:
                    avail_lim = 0.0
                if avail_lim > lim:
                    conn.close()
                    notify("Kullanılabilir limit, toplam limitten büyük olamaz!", DANGER)
                    return
            except Exception:
                avail_lim = lim

            total_blocked_debt = max(0.0, lim - avail_lim)
            try:
                p_debt = float((new_acc_period_debt.value or "0").replace(",", "."))
                p_debt = min(total_blocked_debt, max(0.0, p_debt))
            except Exception:
                p_debt = 0.0

            cur.execute(
                "INSERT INTO accounts (name, type, balance, total_limit, current_debt, period_debt, color, icon) VALUES (?, ?, 0.0, ?, ?, ?, '#6366F1', 'credit_card')",
                (name, acc_t, lim, total_blocked_debt, p_debt)
            )
            toast_msg = f"'{name}' eklendi! (Bu Ay Ödenecek: {format_tl(p_debt)} | İleri Taksit Blokesi: {format_tl(total_blocked_debt - p_debt)}) 💳"
        else:
            try:
                bal = float(new_acc_balance.value.replace(",", "."))
            except Exception:
                bal = 0.0
            color = "#10B981" if acc_t == "Nakit" else "#0284C7"
            icon = "payments" if acc_t == "Nakit" else "account_balance"
            cur.execute(
                "INSERT INTO accounts (name, type, balance, total_limit, current_debt, period_debt, color, icon) VALUES (?, ?, ?, 0.0, 0.0, 0.0, ?, ?)",
                (name, acc_t, bal, color, icon)
            )
            toast_msg = f"'{name}' hesabı eklendi! 🏦"

        conn.commit()
        conn.close()
        
        new_acc_name.value = ""
        new_acc_balance.value = "0"
        new_acc_limit.value = "50000"
        new_acc_avail_limit.value = "50000"
        new_acc_debt_installments.value = "3"
        new_acc_period_debt.value = "0"
        close_popup(add_account_dialog)
        render_current_view()
        notify(toast_msg, ACCENT)
        page.update()

    add_account_dialog = ft.AlertDialog(
        title=ft.Text("Yeni Hesap / Kredi Kartı Tanımla", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                new_acc_type,
                new_acc_name,
                new_acc_balance,
                new_acc_limit,
                new_acc_avail_limit,
                new_acc_debt_installments,
                new_acc_period_debt,
                cc_debt_preview,
                cc_info_note
            ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
            width=360,
        ),
        actions=[
            TextButton("Vazgeç", on_click=lambda e: close_popup(add_account_dialog)),
            Button("Kaydet", bgcolor=PRIMARY, color="white", on_click=save_new_account)
        ]
    )

    # 2A. KREDİ KARTI TOPLAM LİMİT, KULLANILABİLİR LİMİT & BU AYKİ DÖNEM BORCU DÜZENLEME DİYALOGU
    active_cc_edit = {"id": None, "name": ""}
    edit_cc_total_limit = ft.TextField(label="Toplam Kart Limiti (₺)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    edit_cc_avail_limit = ft.TextField(label="Kullanılabilir Limit (₺)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    edit_cc_installment_plan = ft.Dropdown(
        label="Kullanılan Limit (Fark) Kaç Taksit?",
        options=[
            Option("0", "Manuel (Bu Ay Ödenecek Tutarı Kendim Gireceğim)"),
            Option("1", "Tek Çekim (Tamamı Bu Ay Ödenecek)"),
            Option("2", "2 Taksit (Aylık Eşit Böl)"),
            Option("3", "3 Taksit (Aylık Eşit Böl)"),
            Option("4", "4 Taksit (Aylık Eşit Böl)"),
            Option("6", "6 Taksit (Aylık Eşit Böl)"),
            Option("9", "9 Taksit (Aylık Eşit Böl)"),
            Option("12", "12 Taksit (Aylık Eşit Böl)"),
        ],
        value="0",
        border_radius=10,
    )
    edit_cc_period_debt = ft.TextField(label="Bu Ay Ödenecek Dönem Borcu / Ekstre (₺)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    edit_cc_debt_info = ft.Text("", size=11.5, color=WARNING, weight=ft.FontWeight.BOLD)

    def update_edit_cc_debt_info(from_plan=False):
        try:
            t_l = float((edit_cc_total_limit.value or "0").replace(",", "."))
            a_l = float((edit_cc_avail_limit.value or "0").replace(",", "."))
            total_blocked = max(0.0, t_l - a_l)
            plan_inst = int(edit_cc_installment_plan.value or "0")
            if from_plan and plan_inst > 0:
                edit_cc_period_debt.value = str(round(total_blocked / plan_inst, 2))
            p_debt = min(total_blocked, max(0.0, float((edit_cc_period_debt.value or "0").replace(",", "."))))
            future_block = max(0.0, total_blocked - p_debt)
            edit_cc_debt_info.value = (
                f"📌 Toplam Limit Blokesi: {format_tl(total_blocked)}\n"
                f"💳 Bu Ay Ödenecek: {format_tl(p_debt)} | ⏳ İleri Taksitler: {format_tl(future_block)}"
            )
        except Exception:
            edit_cc_debt_info.value = "📌 Toplam Limit Blokesi: 0,00 ₺"
        page.update()

    edit_cc_total_limit.on_change = lambda e: update_edit_cc_debt_info(True)
    edit_cc_avail_limit.on_change = lambda e: update_edit_cc_debt_info(True)
    edit_cc_installment_plan.on_change = lambda e: update_edit_cc_debt_info(True)
    edit_cc_period_debt.on_change = lambda e: (setattr(edit_cc_installment_plan, "value", "0"), update_edit_cc_debt_info(False))

    def open_edit_cc_limits_dialog(card_id, card_name, total_limit, avail_limit, period_debt):
        active_cc_edit["id"] = card_id
        active_cc_edit["name"] = card_name
        edit_cc_total_limit.value = str(round(total_limit, 2))
        edit_cc_avail_limit.value = str(round(avail_limit, 2))
        edit_cc_installment_plan.value = "0"
        edit_cc_period_debt.value = str(round(period_debt, 2))
        update_edit_cc_debt_info(False)
        show_popup(edit_cc_limit_dialog)

    def submit_edit_cc_limits(e):
        try:
            t_lim = float(edit_cc_total_limit.value.replace(",", "."))
            a_lim = float(edit_cc_avail_limit.value.replace(",", "."))
            if t_lim <= 0:
                notify("Toplam limit 0'dan büyük olmalıdır!", DANGER)
                return
            if a_lim < 0 or a_lim > t_lim:
                notify("Kullanılabilir limit 0 ile Toplam Limit arasında olmalıdır!", DANGER)
                return
        except Exception:
            notify("Lütfen geçerli sayısal limit değerleri giriniz!", DANGER)
            return

        new_blocked_debt = max(0.0, t_lim - a_lim)
        try:
            p_debt = float((edit_cc_period_debt.value or "0").replace(",", "."))
            p_debt = min(new_blocked_debt, max(0.0, p_debt))
        except Exception:
            p_debt = 0.0

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE accounts SET total_limit = ?, current_debt = ?, period_debt = ? WHERE id = ?",
            (t_lim, new_blocked_debt, p_debt, active_cc_edit["id"])
        )
        conn.commit()
        conn.close()
        close_popup(edit_cc_limit_dialog)
        notify(f"'{active_cc_edit['name']}' güncellendi! (Bu Ay Ödenecek: {format_tl(p_debt)} | İleri Taksit Blokesi: {format_tl(new_blocked_debt - p_debt)}) 💳", ACCENT)
        render_current_view()
        page.update()

    edit_cc_limit_dialog = ft.AlertDialog(
        title=ft.Text("💳 Kart Limit & Taksit Borcu Düzenle", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                edit_cc_total_limit,
                edit_cc_avail_limit,
                edit_cc_installment_plan,
                edit_cc_period_debt,
                edit_cc_debt_info,
            ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
            width=360,
        ),
        actions=[
            TextButton("İptal", on_click=lambda e: close_popup(edit_cc_limit_dialog)),
            Button("Güncelle", bgcolor=PRIMARY, color="white", on_click=submit_edit_cc_limits),
        ]
    )

    # 2B. KREDİ KARTI BORCU ÖDEME DİYALOGU
    active_cc_pay = {"id": None, "name": ""}
    cc_pay_info_text = ft.Text("", size=11.5, color=ACCENT)
    cc_pay_amount = ft.TextField(label="Bu Ay Ödenecek Tutar (₺)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    cc_pay_source = ft.Dropdown(label="Ödemenin Çekileceği Nakit/Banka Hesabı", border_radius=10)

    def open_pay_cc_dialog(card_id, card_name, current_debt, period_debt):
        active_cc_pay["id"] = card_id
        active_cc_pay["name"] = card_name
        default_pay = period_debt if period_debt > 0 else current_debt
        cc_pay_amount.value = str(round(default_pay, 2))
        future_block = max(0.0, current_debt - period_debt)
        cc_pay_info_text.value = (
            f"💳 Bu Ayki Dönem Borcu: {format_tl(period_debt)}\n"
            f"⏳ Gelecek Aylar Taksit Blokesi: {format_tl(future_block)}"
        )
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, balance FROM accounts WHERE type IN ('Nakit', 'Banka')")
        bank_accs = cur.fetchall()
        conn.close()

        opts = [Option("0", "Hesaptan Düşme (Harici Ödeme)")]
        for b in bank_accs:
            opts.append(Option(str(b["id"]), f"{b['name']} ({format_tl(b['balance'])})"))
        cc_pay_source.options = opts
        cc_pay_source.value = str(bank_accs[0]["id"]) if bank_accs else "0"
        show_popup(pay_cc_dialog)

    def submit_cc_payment(e):
        try:
            pay_val = float(cc_pay_amount.value.replace(",", "."))
            if pay_val <= 0:
                notify("Geçerli bir ödeme tutarı giriniz!", DANGER)
                return
        except Exception:
            notify("Lütfen sayısal bir tutar giriniz!", DANGER)
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE accounts SET current_debt = MAX(0.0, current_debt - ?), period_debt = MAX(0.0, period_debt - ?) WHERE id = ?",
            (pay_val, pay_val, active_cc_pay["id"])
        )
        
        src_id = int(cc_pay_source.value or "0")
        if src_id > 0:
            cur.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (pay_val, src_id))
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            cur.execute("""
            INSERT INTO transactions (account_id, title, amount, category, date, type, total_installments, installment_index)
            VALUES (?, ?, ?, 'Faturalar & Abonelik', ?, 'Gider', 1, 1)
            """, (src_id, f"{active_cc_pay['name']} Dönem Borcu Ödemesi", pay_val, today_str))

        conn.commit()
        conn.close()
        close_popup(pay_cc_dialog)
        notify(f"'{active_cc_pay['name']}' kartına {format_tl(pay_val)} ödeme yapıldı, kullanılabilir limit açıldı! 🎉", ACCENT)
        render_current_view()
        page.update()

    pay_cc_dialog = ft.AlertDialog(
        title=ft.Text("💳 Kredi Kartı Dönem Borcu Öde", weight=ft.FontWeight.BOLD),
        content=ft.Column([
            cc_pay_info_text,
            cc_pay_amount,
            cc_pay_source,
        ], tight=True, spacing=12),
        actions=[
            TextButton("İptal", on_click=lambda e: close_popup(pay_cc_dialog)),
            Button("Ödemeyi Yap", bgcolor=ACCENT, color="white", on_click=submit_cc_payment),
        ]
    )

    # 3. YENİ BİRİKİM HEDEFI EKLE DİYALOGU
    new_goal_title = ft.TextField(label="Hedef Başlığı (örn: Tatil, iPhone 16)", border_radius=10)
    new_goal_target = ft.TextField(label="Hedef Tutar (₺)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    new_goal_init = ft.TextField(label="Şu Anda Biriken (₺)", value="0", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)

    def save_new_goal(e):
        title = new_goal_title.value.strip()
        if not title:
            notify("Hedef adı boş olamaz!", DANGER)
            return
        try:
            target = float(new_goal_target.value.replace(",", "."))
            curr = float(new_goal_init.value.replace(",", "."))
        except Exception:
            notify("Geçerli sayılar giriniz!", DANGER)
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO savings_goals (title, target_amount, current_amount) VALUES (?, ?, ?)", (title, target, curr))
        conn.commit()
        conn.close()
        
        new_goal_title.value = ""
        new_goal_target.value = ""
        new_goal_init.value = "0"
        close_popup(add_goal_dialog)
        notify(f"'{title}' hedefi oluşturuldu! 🚀", ACCENT)
        render_current_view()
        page.update()

    add_goal_dialog = ft.AlertDialog(
        title=ft.Text("Yeni Birikim Hedefi"),
        content=ft.Column([
            new_goal_title,
            new_goal_target,
            new_goal_init
        ], tight=True, spacing=12),
        actions=[
            TextButton("İptal", on_click=lambda e: close_popup(add_goal_dialog)),
            Button("Oluştur", bgcolor=PRIMARY, color="white", on_click=save_new_goal)
        ]
    )

    # 4. HEDEFE PARA EKLE DIALOGU
    active_goal_id = {"id": None}
    deposit_amount_field = ft.TextField(label="Eklenecek Tutar (₺)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)

    def deposit_to_goal_submit(e):
        try:
            dep_val = float(deposit_amount_field.value.replace(",", "."))
        except Exception:
            notify("Geçerli tutar giriniz!", DANGER)
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, title, target_amount, current_amount FROM savings_goals WHERE id = ?", (active_goal_id["id"],))
        g = cur.fetchone()
        if g:
            new_val = g["current_amount"] + dep_val
            cur.execute("UPDATE savings_goals SET current_amount = ? WHERE id = ?", (new_val, g["id"]))
            conn.commit()
            
            close_popup(deposit_goal_dialog)
            if new_val >= g["target_amount"] and g["current_amount"] < g["target_amount"]:
                show_celebration(g["title"])
            else:
                notify(f"{format_tl(dep_val)} birikime eklendi! 🎉", ACCENT)
        conn.close()
        
        deposit_amount_field.value = ""
        render_current_view()
        page.update()

    deposit_goal_dialog = ft.AlertDialog(
        title=ft.Text("Hedefe Para Ekle"),
        content=deposit_amount_field,
        actions=[
            TextButton("İptal", on_click=lambda e: close_popup(deposit_goal_dialog)),
            Button("Aktar", bgcolor=ACCENT, color="white", on_click=deposit_to_goal_submit)
        ]
    )

    def show_celebration(goal_name):
        cel_dialog = ft.AlertDialog(
            title=ft.Text("TEBRİKLER! 🥳🎉", weight=ft.FontWeight.BOLD, color=ACCENT, text_align=ft.TextAlign.CENTER),
            content=ft.Column([
                ft.Icon(Icons.EMOJI_EVENTS, size=70, color="#F59E0B"),
                ft.Text(f"'{goal_name}' hedefine başarıyla ulaştın!", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Finans koçun seninle gurur duyuyor! Disiplinli birikim alışkanlığın ödülünü verdi.", size=13, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER)
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                Button("Harika!", bgcolor=PRIMARY, color="white", on_click=lambda e: close_popup(cel_dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
        show_popup(cel_dialog)

    # 5. YENİ ABONELİK EKLE DIALOGU
    new_sub_name = ft.TextField(label="Hizmet / Abonelik Adı (örn: YouTube, Kira)", border_radius=10)
    new_sub_amount = ft.TextField(label="Aylık Tutar (₺)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
    new_sub_day = ft.TextField(label="Ödeme Günü (Ayın 1-31'i)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)

    def save_new_subscription(e):
        name = new_sub_name.value.strip()
        if not name:
            notify("Abonelik adını giriniz!", DANGER)
            return
        try:
            amt = float(new_sub_amount.value.replace(",", "."))
            day = int(new_sub_day.value)
            if day < 1 or day > 31:
                notify("Gün 1 ile 31 arasında olmalıdır!", DANGER)
                return
        except Exception:
            notify("Lütfen sayısal alanları kontrol edin!", DANGER)
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO subscriptions (name, amount, billing_day, category) VALUES (?, ?, ?, ?)", (name, amt, day, "Sabit Gider"))
        conn.commit()
        conn.close()
        
        new_sub_name.value = ""
        new_sub_amount.value = ""
        new_sub_day.value = ""
        close_popup(add_sub_dialog)
        notify(f"'{name}' aboneliği eklendi! 📅", ACCENT)
        render_current_view()
        page.update()

    add_sub_dialog = ft.AlertDialog(
        title=ft.Text("Yeni Sabit Gider / Abonelik"),
        content=ft.Column([
            new_sub_name,
            new_sub_amount,
            new_sub_day
        ], tight=True, spacing=12),
        actions=[
            TextButton("İptal", on_click=lambda e: close_popup(add_sub_dialog)),
            Button("Kaydet", bgcolor=PRIMARY, color="white", on_click=save_new_subscription)
        ]
    )

    # 6. BÖLÜMSEL VE TEKİL VERİ SIFIRLAMA / SİLME SİSTEMİ
    def confirm_action(title, message, on_confirm):
        def do_confirm(e):
            close_popup(conf_dialog)
            on_confirm()
            render_current_view()
            page.update()

        conf_dialog = ft.AlertDialog(
            title=ft.Text(f"⚠️ {title}", weight=ft.FontWeight.BOLD, color=DANGER),
            content=ft.Text(message, size=13.5),
            actions=[
                TextButton("Vazgeç", on_click=lambda e: close_popup(conf_dialog)),
                Button("Evet, Onayla", bgcolor=DANGER, color="white", on_click=do_confirm),
            ]
        )
        show_popup(conf_dialog)

    def reset_all_data():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions")
        cur.execute("DELETE FROM receivables")
        cur.execute("DELETE FROM subscriptions")
        cur.execute("DELETE FROM savings_goals")
        cur.execute("DELETE FROM accounts")
        conn.commit()
        conn.close()
        notify("Tüm bankalar, hesaplar ve veriler sıfırlandı! 🔄", DANGER)

    def reset_goals_data():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM savings_goals")
        conn.commit()
        conn.close()
        notify("Tüm birikim hedefleri sıfırlandı! 🎯", WARNING)

    def delete_single_goal(gid, title):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM savings_goals WHERE id = ?", (gid,))
        conn.commit()
        conn.close()
        notify(f"'{title}' hedefi silindi! 🗑️", ACCENT)

    def reset_single_goal_progress(gid, title):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE savings_goals SET current_amount = 0.0 WHERE id = ?", (gid,))
        conn.commit()
        conn.close()
        notify(f"'{title}' hedefinin birikimi 0 ₺ olarak sıfırlandı! 🔄", ACCENT)

    def reset_transactions_data():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions")
        conn.commit()
        conn.close()
        notify("Tüm işlem ve taksit geçmişi sıfırlandı! 💳", WARNING)

    def delete_single_transaction(tid, title, amount, t_type, acc_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id = ?", (tid,))
        if acc_id:
            cur.execute("SELECT type FROM accounts WHERE id = ?", (acc_id,))
            acc_row = cur.fetchone()
            if acc_row and acc_row["type"] == "Kredi Kartı":
                if t_type == "Gider":
                    cur.execute(
                        "UPDATE accounts SET current_debt = MAX(0.0, current_debt - ?), period_debt = MAX(0.0, period_debt - ?) WHERE id = ?",
                        (amount, amount, acc_id)
                    )
            else:
                if t_type == "Gider":
                    cur.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, acc_id))
                elif t_type == "Gelir":
                    cur.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, acc_id))
        conn.commit()
        conn.close()
        notify(f"'{title}' işlemi silindi ve bakiye/limit güncellendi! 🗑️", ACCENT)

    def reset_subscriptions_data():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM subscriptions")
        conn.commit()
        conn.close()
        notify("Tüm sabit gider ve abonelikler sıfırlandı! 📅", WARNING)

    def delete_single_subscription(sid, name):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM subscriptions WHERE id = ?", (sid,))
        conn.commit()
        conn.close()
        notify(f"'{name}' aboneliği silindi! 🗑️", ACCENT)

    def reset_receivables_data():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM receivables")
        conn.commit()
        conn.close()
        notify("Tüm ortak harcama ve alacak kayıtları sıfırlandı! 🤝", WARNING)

    def delete_single_receivable(rid, title):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM receivables WHERE id = ?", (rid,))
        conn.commit()
        conn.close()
        notify(f"'{title}' kaydı silindi! 🗑️", ACCENT)

    def reset_accounts_data():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM accounts")
        conn.commit()
        conn.close()
        notify("Tüm banka ve kart hesapları silindi! 🏦", WARNING)

    def delete_single_account(acc_id, name):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM accounts WHERE id = ?", (acc_id,))
        conn.commit()
        conn.close()
        notify(f"'{name}' hesabı/kartı silindi! 🗑️", ACCENT)

    def reset_balances_only():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET balance = 0.0, current_debt = 0.0, period_debt = 0.0")
        conn.commit()
        conn.close()
        notify("Tüm hesap bakiyeleri ve kart borçları 0,00 ₺ olarak sıfırlandı! 💰", WARNING)

    def reset_single_cc_debt(card_id, card_name):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET current_debt = 0.0, period_debt = 0.0 WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()
        notify(f"'{card_name}' kartının tüm dönem ve taksit borçları 0,00 ₺ olarak sıfırlandı! 🔄", ACCENT)

    reset_hub_dialog = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(Icons.DELETE_SWEEP, color=DANGER, size=24),
            ft.Text("Sıfırlama Merkezi", weight=ft.FontWeight.BOLD, color="white"),
        ], spacing=8),
        content=ft.Container(
            content=ft.Column([
                ft.Text("Sadece istediğiniz sekmeyi veya tüm uygulamayı sıfırlayabilirsiniz:", size=12.5, color=TEXT_MUTED),
                ft.Divider(color="#334155"),
                Button(
                    "🎯 Sadece Birikim Hedeflerini Sıfırla",
                    bgcolor="#1E293B",
                    color="white",
                    on_click=lambda e: (close_popup(reset_hub_dialog), confirm_action("Birikim Hedeflerini Sıfırla", "Tüm birikim hedefleriniz silinecektir. Emin misiniz?", reset_goals_data))
                ),
                Button(
                    "💳 Sadece İşlem & Taksitleri Sıfırla",
                    bgcolor="#1E293B",
                    color="white",
                    on_click=lambda e: (close_popup(reset_hub_dialog), confirm_action("İşlemleri Sıfırla", "Tüm gelir, gider ve taksit geçmişiniz silinecektir. Emin misiniz?", reset_transactions_data))
                ),
                Button(
                    "📅 Sadece Abonelikleri Sıfırla",
                    bgcolor="#1E293B",
                    color="white",
                    on_click=lambda e: (close_popup(reset_hub_dialog), confirm_action("Abonelikleri Sıfırla", "Tüm sabit gider ve abonelikleriniz silinecektir. Emin misiniz?", reset_subscriptions_data))
                ),
                Button(
                    "🤝 Sadece Bölüşüm & Alacakları Sıfırla",
                    bgcolor="#1E293B",
                    color="white",
                    on_click=lambda e: (close_popup(reset_hub_dialog), confirm_action("Alacakları Sıfırla", "Tüm ortak harcama ve alacak kayıtlarınız silinecektir. Emin misiniz?", reset_receivables_data))
                ),
                Button(
                    "🏦 Sadece Banka & Kartları Sil",
                    bgcolor="#1E293B",
                    color="white",
                    on_click=lambda e: (close_popup(reset_hub_dialog), confirm_action("Bankaları ve Kartları Sil", "Tanımlı tüm banka ve kredi kartı hesaplarınız silinecektir. Emin misiniz?", reset_accounts_data))
                ),
                Button(
                    "💰 Bakiyeleri ve Kart Borçlarını 0 ₺ Yap",
                    bgcolor="#1E293B",
                    color="white",
                    on_click=lambda e: (close_popup(reset_hub_dialog), confirm_action("Bakiyeleri & Borçları Sıfırla", "Bankalarınız ve kartlarınız silinmeyecek; yalnızca hesap bakiyeleri ve kredi kartı borçları 0,00 ₺ yapılacaktır. Emin misiniz?", reset_balances_only))
                ),
                ft.Divider(color="#334155"),
                Button(
                    "⚠️ TÜM VERİLERİ SIFIRLA (Genel)",
                    bgcolor=DANGER,
                    color="white",
                    on_click=lambda e: (close_popup(reset_hub_dialog), confirm_action("Genel Sıfırlama (Fabrika Ayarları)", "Tüm bankalar, kartlar, işlemler, taksitler, abonelikler ve hedefler tamamen silinecektir. Emin misiniz?", reset_all_data))
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            width=360,
            height=430,
        ),
        actions=[
            TextButton("Kapat", on_click=lambda e: close_popup(reset_hub_dialog)),
        ]
    )

    # 7. İNTERAKTİF AYLIK FİNANS TAKVİMİ & TARİH KALİBRASYONU
    cal_state = {"year": get_active_date().year, "month": get_active_date().month}
    cal_grid_container = ft.Column(spacing=6, tight=True)
    cal_header_title = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="white")
    cal_summary_subtitle = ft.Text("", size=11.5, color=ACCENT)

    def on_system_date_picker_change(e):
        if app_date_picker.value:
            picked = app_date_picker.value
            if isinstance(picked, datetime.datetime):
                picked = picked.date()
            set_active_date(picked)
            cal_state["year"] = picked.year
            cal_state["month"] = picked.month
            close_popup(calendar_dialog)
            render_current_view()
            notify(f"Uygulama takvimi '{format_turkish_date(picked)}' olarak güncellendi! 📅", ACCENT)
            page.update()

    app_date_picker = ft.DatePicker(
        first_date=datetime.date(2024, 1, 1),
        last_date=datetime.date(2030, 12, 31),
        help_text="Bugünün Tarihini Seçin (Takvim Senkronizasyonu)",
        cancel_text="İptal",
        confirm_text="Tarihi Ayarla",
        on_change=on_system_date_picker_change
    )

    def select_calendar_day(day_num):
        target = datetime.date(cal_state["year"], cal_state["month"], day_num)
        set_active_date(target)
        close_popup(calendar_dialog)
        render_current_view()
        _, m_days = calendar.monthrange(target.year, target.month)
        rem = max(0, m_days - target.day)
        notify(f"Tarih: {format_turkish_date(target)} ({TURKISH_MONTHS[target.month]} ayının bitmesine {rem} gün kaldı) 📅", ACCENT)
        page.update()

    def build_calendar_grid():
        active_d = get_active_date()
        y, m = cal_state["year"], cal_state["month"]
        first_weekday, num_days = calendar.monthrange(y, m)
        month_name = TURKISH_MONTHS[m]
        cal_header_title.value = f"📅 {month_name} {y} ({num_days} Gün)"

        if y == active_d.year and m == active_d.month:
            rem_d = max(0, num_days - active_d.day)
            cal_summary_subtitle.value = f"Bugün: {active_d.day} {month_name} ({TURKISH_DAYS[active_d.weekday()]}) • Ay Sonuna Kalan: {rem_d} Gün"
        else:
            cal_summary_subtitle.value = f"Seçili Ay: {month_name} {y} • Toplam {num_days} Gün Çekiyor"

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT billing_day, name FROM subscriptions")
        sub_days = {}
        for s in cur.fetchall():
            sub_days.setdefault(s["billing_day"], []).append(s["name"])
        conn.close()

        day_headers = ft.Row([
            ft.Container(
                content=ft.Text(d_name, size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                width=40,
                alignment=align.center
            ) for d_name in TURKISH_DAYS_SHORT
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        rows = [day_headers]
        month_cal = calendar.monthcalendar(y, m)
        for week in month_cal:
            week_cells = []
            for day_val in week:
                if day_val == 0:
                    week_cells.append(ft.Container(width=40, height=38))
                else:
                    is_today = (y == active_d.year and m == active_d.month and day_val == active_d.day)
                    has_sub = day_val in sub_days
                    is_past = (y == active_d.year and m == active_d.month and day_val < active_d.day)

                    bg = ACCENT if is_today else ("#312E81" if has_sub else ("#0F172A" if is_past else "#1E293B"))
                    txt_color = "white" if (is_today or has_sub or not is_past) else "#64748B"
                    bdr = border.all(1.5, "white" if is_today else ("#F59E0B" if has_sub else "#334155"))

                    week_cells.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(str(day_val), size=12, weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL, color=txt_color),
                            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                            width=40,
                            height=38,
                            border_radius=8,
                            bgcolor=bg,
                            border=bdr,
                            alignment=align.center,
                            tooltip=f"{day_val} {month_name} {y} (Bugün olarak ayarlamak için dokunun)" + (f" • Ödeme: {', '.join(sub_days[day_val])}" if has_sub else ""),
                            on_click=lambda e, dv=day_val: select_calendar_day(dv)
                        )
                    )
            rows.append(ft.Row(week_cells, alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

        cal_grid_container.controls = rows

    def change_cal_month(delta):
        m = cal_state["month"] + delta
        y = cal_state["year"]
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        cal_state["month"] = m
        cal_state["year"] = y
        build_calendar_grid()
        page.update()

    def open_calendar_dialog(e=None):
        active_d = get_active_date()
        cal_state["year"] = active_d.year
        cal_state["month"] = active_d.month
        build_calendar_grid()
        show_popup(calendar_dialog)

    calendar_dialog = ft.AlertDialog(
        title=ft.Row([
            cal_header_title,
            ft.Row([
                ft.IconButton(icon=Icons.CHEVRON_LEFT, icon_color="white", icon_size=20, tooltip="Önceki Ay", on_click=lambda e: change_cal_month(-1)),
                ft.IconButton(icon=Icons.CHEVRON_RIGHT, icon_color="white", icon_size=20, tooltip="Sonraki Ay", on_click=lambda e: change_cal_month(1)),
            ], spacing=0)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        content=ft.Container(
            content=ft.Column([
                cal_summary_subtitle,
                ft.Divider(color="#334155"),
                cal_grid_container,
                ft.Divider(color="#334155"),
                ft.Text("💡 İpucu: Cihazınızın tarihi farklıysa takvimden bugünün gününe dokunarak uygulamayı anında senkronize edebilirsiniz.", size=11, color=TEXT_MUTED),
            ], tight=True, spacing=8),
            width=340,
        ),
        actions=[
            TextButton("Tarih Seçici", on_click=lambda e: (setattr(app_date_picker, "value", get_active_date()), show_popup(app_date_picker))),
            Button("Kapat", bgcolor=PRIMARY, color="white", on_click=lambda e: close_popup(calendar_dialog)),
        ]
    )

    # ==========================================
    # SEKMELERİN GÖRÜNÜMLERİ (VIEWS)
    # ==========================================

    main_content_area = ft.Container(expand=True)

    # SEKME 0: DASHBOARD & FİNANS KOÇU
    def view_dashboard():
        metrics = calculate_coach_metrics()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE type IN ('Nakit', 'Banka')")
        liquid_accounts = cur.fetchall()
        cur.execute("SELECT * FROM accounts WHERE type = 'Kredi Kartı'")
        credit_cards = cur.fetchall()
        conn.close()

        # 1. Nakit ve Banka Hesap Kartları (Toplam Bakiyeye Dahil Olanlar)
        acc_cards = []
        for acc in liquid_accounts:
            icon_name = Icons.PAYMENTS if acc["type"] == "Nakit" else Icons.ACCOUNT_BALANCE
            acc_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(icon_name, color="white", size=18),
                                ft.Text(acc["type"], size=11, color="#E2E8F0", weight=ft.FontWeight.W_500)
                            ], spacing=4),
                            ft.IconButton(
                                icon=Icons.CLOSE,
                                icon_color="#CBD5E1",
                                icon_size=14,
                                tooltip="Bu Hesabı Sil",
                                on_click=lambda e, aid=acc["id"], aname=acc["name"]: confirm_action("Hesabı Sil", f"'{aname}' hesabını silmek istediğinize emin misiniz?", lambda: delete_single_account(aid, aname))
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(acc["name"], size=13, color="white", weight=ft.FontWeight.BOLD),
                        ft.Text(format_tl(acc["balance"]), size=15, color="white", weight=ft.FontWeight.BOLD),
                    ], spacing=4),
                    width=160,
                    padding=12,
                    border_radius=12,
                    gradient=ft.LinearGradient(
                        begin=align.top_left,
                        end=align.bottom_right,
                        colors=[acc["color"] or "#0284C7", "#0F172A"]
                    )
                )
            )

        if not acc_cards:
            acc_cards.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(Icons.ACCOUNT_BALANCE_WALLET, color=ACCENT, size=22),
                        ft.Text("Nakit veya Banka hesabı eklemek için dokunun.", size=12, color=TEXT_MUTED)
                    ], spacing=10),
                    padding=14,
                    border_radius=12,
                    bgcolor=CARD_BG,
                    border=border.all(1, "#334155"),
                    on_click=lambda e: open_add_account_modal("Banka")
                )
            )

        # 2. Kredi Kartlarım (Toplam Limit, Kullanılabilir Limit, Bu Ay Ödenecek Borç & İleri Taksit Blokesi Ayrımlı)
        cc_widgets = []
        for cc in credit_cards:
            t_limit = cc["total_limit"] or 0.0
            c_debt = cc["current_debt"] or 0.0  # Toplam kullanılan (bloke) limit
            p_debt = cc["period_debt"] if "period_debt" in cc.keys() and cc["period_debt"] is not None else 0.0
            p_debt = min(c_debt, max(0.0, p_debt))
            future_installment_debt = max(0.0, c_debt - p_debt)
            avail_limit = max(0.0, t_limit - c_debt)
            usage_ratio = min(1.0, c_debt / t_limit) if t_limit > 0 else 0.0
            usage_pct = int(usage_ratio * 100)
            bar_color = DANGER if usage_pct >= 80 else (WARNING if usage_pct >= 50 else ACCENT)

            cc_widgets.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(Icons.CREDIT_CARD, color="#818CF8", size=22),
                                ft.Column([
                                    ft.Text(cc["name"], size=15, weight=ft.FontWeight.BOLD, color="white"),
                                    ft.Text("Borçlanma Aracı • Nakit Bakiyeye Eklenmez", size=10, color=TEXT_MUTED),
                                ], spacing=1),
                            ], spacing=8),
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(f"%{usage_pct} Bloke", size=10.5, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor=bar_color,
                                    padding=pad.symmetric(horizontal=8, vertical=3),
                                    border_radius=8
                                ),
                                ft.IconButton(
                                    icon=Icons.EDIT,
                                    icon_color="#818CF8",
                                    icon_size=17,
                                    tooltip="Limitleri ve Bu Ay Ödenecek Taksit/Dönem Borcunu Düzenle",
                                    on_click=lambda e, cid=cc["id"], cname=cc["name"], tlim=t_limit, alim=avail_limit, pdebt=p_debt: open_edit_cc_limits_dialog(cid, cname, tlim, alim, pdebt)
                                ),
                                ft.IconButton(
                                    icon=Icons.RESTART_ALT,
                                    icon_color=WARNING,
                                    icon_size=17,
                                    tooltip="Kart Borcunu Sıfırla (Kullanılabilir Limiti Tam Doldur)",
                                    on_click=lambda e, cid=cc["id"], cname=cc["name"]: confirm_action("Kart Borcunu Sıfırla", f"'{cname}' kartının borcunu 0,00 ₺ yapıp kullanılabilir limitini tam limite eşitlemek istiyor musunuz?", lambda: reset_single_cc_debt(cid, cname))
                                ),
                                ft.IconButton(
                                    icon=Icons.DELETE_OUTLINE,
                                    icon_color=DANGER,
                                    icon_size=17,
                                    tooltip="Bu Kredi Kartını Sil",
                                    on_click=lambda e, cid=cc["id"], cname=cc["name"]: confirm_action("Kredi Kartını Sil", f"'{cname}' kredi kartını silmek istiyor musunuz?", lambda: delete_single_account(cid, cname))
                                ),
                            ], spacing=0)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                        # TOPLAM LİMİT & KULLANILABİLİR LİMİT AYRI KART KUTULARI
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("TOPLAM LİMİT", size=10, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                                    ft.Text(format_tl(t_limit), size=14.5, weight=ft.FontWeight.BOLD, color="#E2E8F0"),
                                ], spacing=3),
                                padding=10,
                                border_radius=10,
                                bgcolor="#0F172A",
                                border=border.all(1, "#334155"),
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("KULLANILABİLİR LİMİT", size=10, color=ACCENT, weight=ft.FontWeight.BOLD),
                                    ft.Text(format_tl(avail_limit), size=14.5, weight=ft.FontWeight.BOLD, color=ACCENT),
                                ], spacing=3),
                                padding=10,
                                border_radius=10,
                                bgcolor="#0F172A",
                                border=border.all(1, "#10B981"),
                                expand=True,
                            ),
                        ], spacing=8),

                        ft.ProgressBar(value=usage_ratio, color=bar_color, bgcolor="#0F172A"),

                        # BU AY ÖDENECEK DÖNEM BORCU vs İLERİ AYLAR TAKSİT BLOKESİ AYRIMI
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("💳 Bu Ay Ödenecek Dönem Borcu:", size=11.5, color="white", weight=ft.FontWeight.W_500),
                                    ft.Text(format_tl(p_debt), size=13, weight=ft.FontWeight.BOLD, color=DANGER if p_debt > 0 else ACCENT),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Row([
                                    ft.Text("⏳ İleri Aylar Taksit Blokesi (Şimdi Ödenmez):", size=11, color=TEXT_MUTED),
                                    ft.Text(format_tl(future_installment_debt), size=11.5, weight=ft.FontWeight.BOLD, color=WARNING if future_installment_debt > 0 else TEXT_MUTED),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Row([
                                    ft.Text("📌 Toplam Kullanılan Limit (Bloke):", size=10.5, color=TEXT_MUTED),
                                    ft.Text(format_tl(c_debt), size=11, color="#CBD5E1"),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ], spacing=4),
                            padding=10,
                            border_radius=10,
                            bgcolor="#0F172A",
                            border=border.all(1, "#334155"),
                        ),

                        ft.Row([
                            Button(
                                "💳 Karttan Harca",
                                bgcolor="#312E81",
                                color="white",
                                expand=True,
                                on_click=lambda e, cid=cc["id"]: (refresh_account_dropdown(), setattr(input_account, "value", str(cid)), show_popup(add_transaction_dialog))
                            ),
                            Button(
                                "💰 Dönem Borcu Öde",
                                bgcolor="#065F46" if c_debt > 0 else "#334155",
                                color="white",
                                expand=True,
                                on_click=lambda e, cid=cc["id"], cname=cc["name"], cdebt=c_debt, pdebt=p_debt: open_pay_cc_dialog(cid, cname, cdebt, pdebt) if c_debt > 0 else notify("Bu kartın borcu bulunmuyor! ✨", ACCENT)
                            ),
                        ], spacing=8)
                    ], spacing=10),
                    padding=14,
                    border_radius=14,
                    gradient=ft.LinearGradient(
                        begin=align.top_left,
                        end=align.bottom_right,
                        colors=["#1E293B", "#1E1B4B"]
                    ),
                    border=border.all(1, "#4338CA")
                )
            )

        if not cc_widgets:
            cc_widgets.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(Icons.ADD_CARD, color="#818CF8", size=22),
                        ft.Text("Henüz kredi kartı tanımlanmadı. Toplam ve kullanılabilir limit takibi için ekleyin.", size=12, color=TEXT_MUTED, expand=True)
                    ], spacing=10),
                    padding=14,
                    border_radius=12,
                    bgcolor=CARD_BG,
                    border=border.all(1, "#334155"),
                    on_click=lambda e: open_add_account_modal("Kredi Kartı")
                )
            )

        advice_widgets = [
            ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.AUTO_AWESOME, color="#F59E0B", size=22),
                    ft.Text(adv, size=12.5, color="#E2E8F0", expand=True)
                ], vertical_alignment=ft.CrossAxisAlignment.START),
                padding=10,
                border_radius=10,
                bgcolor="#1E293B",
                border=border.all(1, "#334155")
            ) for adv in metrics["advice"]
        ]

        active_today = metrics["today"]
        m_name = metrics["month_name"]
        m_total_days = metrics["num_days"]
        rem_days = metrics["remaining_days"]

        return ft.ListView([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Icon(Icons.CALENDAR_MONTH, color=ACCENT, size=15),
                                ft.Text(f"{format_turkish_date(active_today)} ({m_name}: {m_total_days} Gün)", size=12, color=ACCENT, weight=ft.FontWeight.W_600),
                            ], spacing=4),
                            ft.Text("Finansal Durumun", size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ], spacing=2),
                        ft.Row([
                            ft.IconButton(
                                icon=Icons.CALENDAR_MONTH,
                                icon_color="#818CF8",
                                tooltip="Aylık Takvim & Tarih Ayarı",
                                on_click=open_calendar_dialog
                            ),
                            ft.IconButton(
                                icon=Icons.DELETE_SWEEP,
                                icon_color=DANGER,
                                tooltip="Sıfırlama Merkezi (Bölümsel veya Genel)",
                                on_click=lambda e: show_popup(reset_hub_dialog)
                            ),
                            ft.IconButton(
                                icon=Icons.ADD_CARD,
                                icon_color=ACCENT,
                                tooltip="Yeni Hesap veya Kart Tanımla",
                                on_click=lambda e: open_add_account_modal("Banka")
                            ),
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Row([
                                    ft.Icon(Icons.SHIELD_OUTLINED, color=ACCENT, size=20),
                                    ft.Text("GÜNLÜK GÜVENLİ LİMİT", size=11, color=ACCENT, weight=ft.FontWeight.BOLD),
                                ], spacing=6),
                                ft.Container(
                                    content=ft.Text(f"📅 {m_name} ({active_today.day}/{m_total_days}) • {rem_days} Gün Kaldı", size=10.5, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor="#065F46",
                                    padding=pad.symmetric(horizontal=9, vertical=3),
                                    border_radius=10,
                                    on_click=open_calendar_dialog,
                                    tooltip="Takvimi açmak veya tarihi kalibre etmek için dokunun"
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(format_tl(metrics["daily_safe_limit"]), size=26, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text(f"{m_name} ayı {m_total_days} gün çekiyor. Ay sonuna kalan {rem_days} gün için günlük güvenli nakit/banka bütçeniz.", size=11, color=TEXT_MUTED)
                        ]),
                        padding=16,
                        border_radius=16,
                        bgcolor="#1E293B",
                        border=border.all(1, "#334155")
                    ),
                ], spacing=12),
                padding=pad.only(left=16, right=16, top=16)
            ),

            # BÖLÜM 1: NAKİT VE BANKA HESAPLARI (TOPLAM BAKİYE)
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Nakit & Banka Hesaplarım", size=15, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(f"Toplam Nakit: {format_tl(metrics['liquid_assets'])}", size=12, color=ACCENT, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row(acc_cards, scroll=ft.ScrollMode.AUTO, spacing=10)
                ], spacing=8),
                padding=pad.symmetric(horizontal=16, vertical=8)
            ),

            # BÖLÜM 2: KREDİ KARTLARIM (LİMİT, GÜNCEL BORÇ VE KALAN LİMİT)
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Icon(Icons.CREDIT_CARD, color="#818CF8", size=18),
                            ft.Text("Kredi Kartlarım", size=15, weight=ft.FontWeight.BOLD, color="white"),
                        ], spacing=6),
                        TextButton(
                            "+ Kart Ekle",
                            on_click=lambda e: open_add_account_modal("Kredi Kartı")
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Column(cc_widgets, spacing=10)
                ], spacing=6),
                padding=pad.symmetric(horizontal=16, vertical=4)
            ),

            ft.Container(
                content=ft.Row([
                    Button(
                        "İşlem Ekle",
                        icon=Icons.ADD,
                        bgcolor=PRIMARY,
                        color="white",
                        expand=True,
                        on_click=lambda e: (refresh_account_dropdown(), show_popup(add_transaction_dialog))
                    ),
                    Button(
                        "Fiş Tara",
                        icon=Icons.DOCUMENT_SCANNER,
                        bgcolor="#334155",
                        color="white",
                        expand=True,
                        on_click=lambda e: (refresh_account_dropdown(), simulate_ocr_scan(), show_popup(add_transaction_dialog))
                    ),
                ], spacing=10),
                padding=pad.symmetric(horizontal=16, vertical=4)
            ),

            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(Icons.PSYCHOLOGY, color=PRIMARY, size=22),
                        ft.Text("Koçun Tavsiyeleri & Analiz", size=15, weight=ft.FontWeight.BOLD, color="white"),
                    ]),
                    ft.Column(advice_widgets, spacing=8)
                ], spacing=10),
                padding=pad.all(16)
            ),
        ], spacing=10, expand=True)

    # SEKME 1: İŞLEMLER & TAKSİTLER
    def view_transactions():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        SELECT t.*, a.name as acc_name FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.id
        ORDER BY t.date DESC, t.id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        items = []
        for r in rows:
            is_expense = r["type"] == "Gider"
            amount_color = DANGER if is_expense else ACCENT
            sign = "-" if is_expense else "+"
            
            badge = None
            if r["total_installments"] > 1:
                badge = ft.Container(
                    content=ft.Text(f"Taksit {r['installment_index']}/{r['total_installments']}", size=10, color="#C7D2FE"),
                    bgcolor="#3730A3",
                    padding=pad.symmetric(horizontal=6, vertical=2),
                    border_radius=6
                )
            elif r["is_shared"]:
                badge = ft.Container(
                    content=ft.Text("Bölüşüldü", size=10, color="#FDE68A"),
                    bgcolor="#854D0E",
                    padding=pad.symmetric(horizontal=6, vertical=2),
                    border_radius=6
                )

            row_header = ft.Row([
                ft.Text(r["title"], size=14, weight=ft.FontWeight.W_600, color="white", expand=True),
                ft.Row([
                    ft.Text(f"{sign}{format_tl(r['amount'])}", size=14, weight=ft.FontWeight.BOLD, color=amount_color),
                    ft.IconButton(
                        icon=Icons.DELETE_OUTLINE,
                        icon_color=TEXT_MUTED,
                        icon_size=18,
                        tooltip="Bu İşlemi Sil",
                        on_click=lambda e, tid=r["id"], ttitle=r["title"], tamt=r["amount"], ttype=r["type"], tacc=r["account_id"]: confirm_action(
                            "İşlemi Sil",
                            f"'{ttitle}' işlemini silmek istiyor musunuz? (Hesap bakiyesi otomatik düzeltilir)",
                            lambda: delete_single_transaction(tid, ttitle, tamt, ttype, tacc)
                        )
                    )
                ], spacing=2)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            sub_info = ft.Row([
                ft.Text(f"{r['date']} • {r['category']} • {r['acc_name'] or 'Silinmiş Hesap'}", size=11, color=TEXT_MUTED),
                badge if badge else ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            items.append(
                ft.Container(
                    content=ft.Column([row_header, sub_info], spacing=4),
                    padding=12,
                    border_radius=10,
                    bgcolor=CARD_BG,
                    border=border.all(1, "#334155")
                )
            )

        if not items:
            items.append(
                ft.Container(
                    content=ft.Text("Henüz kaydedilmiş bir işlem yok.", color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    alignment=align.center,
                    padding=40
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("İşlem & Taksit Geçmişi", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Row([
                        ft.IconButton(
                            icon=Icons.DELETE_SWEEP,
                            icon_color=DANGER,
                            tooltip="Sadece İşlemleri Sıfırla",
                            on_click=lambda e: confirm_action("İşlemleri Sıfırla", "Tüm işlem ve taksit geçmişiniz silinecektir. Emin misiniz?", reset_transactions_data)
                        ),
                        ft.IconButton(
                            icon=Icons.ADD,
                            icon_color=PRIMARY,
                            tooltip="Yeni İşlem Ekle",
                            on_click=lambda e: (refresh_account_dropdown(), show_popup(add_transaction_dialog))
                        ),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ListView(items, spacing=8, expand=True)
            ], spacing=12, expand=True),
            padding=16,
            expand=True
        )

    # SEKME 2: ABONELİKLER & SABİT GİDERLER
    def view_subscriptions():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM subscriptions ORDER BY billing_day ASC")
        subs = cur.fetchall()
        conn.close()

        today_day = get_active_date().day
        total_sub_cost = sum([s["amount"] for s in subs])

        sub_cards = []
        for s in subs:
            b_day = s["billing_day"]
            diff = b_day - today_day
            
            if diff == 0:
                day_badge = ft.Container(content=ft.Text("Bugün Kesilecek!", size=10, color="white"), bgcolor=DANGER, padding=pad.symmetric(horizontal=6, vertical=2), border_radius=6)
            elif 0 < diff <= 3:
                day_badge = ft.Container(content=ft.Text(f"{diff} Gün Kaldı (Yaklaşıyor)", size=10, color="white"), bgcolor=WARNING, padding=pad.symmetric(horizontal=6, vertical=2), border_radius=6)
            elif diff < 0:
                day_badge = ft.Container(content=ft.Text(f"Ödendi (Ayın {b_day}'i)", size=10, color=TEXT_MUTED), bgcolor="#334155", padding=pad.symmetric(horizontal=6, vertical=2), border_radius=6)
            else:
                day_badge = ft.Container(content=ft.Text(f"{diff} Gün Sonra (Ayın {b_day}'i)", size=10, color="#94A3B8"), bgcolor="#1E293B", padding=pad.symmetric(horizontal=6, vertical=2), border_radius=6)

            sub_cards.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(s["name"], size=15, weight=ft.FontWeight.BOLD, color="white"),
                            day_badge
                        ], spacing=6),
                        ft.Row([
                            ft.Text(format_tl(s["amount"]), size=15, weight=ft.FontWeight.BOLD, color="white"),
                            ft.IconButton(
                                icon=Icons.DELETE_OUTLINE,
                                icon_color=TEXT_MUTED,
                                icon_size=18,
                                tooltip="Bu Aboneliği Sil",
                                on_click=lambda e, sid=s["id"], sname=s["name"]: confirm_action("Aboneliği Sil", f"'{sname}' aboneliğini silmek istiyor musunuz?", lambda: delete_single_subscription(sid, sname))
                            )
                        ], spacing=4)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=14,
                    border_radius=12,
                    bgcolor=CARD_BG,
                    border=border.all(1, "#334155")
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Düzenli Abonelikler", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Row([
                        ft.IconButton(
                            icon=Icons.DELETE_SWEEP,
                            icon_color=DANGER,
                            tooltip="Sadece Abonelikleri Sıfırla",
                            on_click=lambda e: confirm_action("Abonelikleri Sıfırla", "Tüm abonelik ve sabit giderleriniz silinecektir. Emin misiniz?", reset_subscriptions_data)
                        ),
                        ft.IconButton(
                            icon=Icons.ADD,
                            icon_color=PRIMARY,
                            tooltip="Yeni Abonelik Ekle",
                            on_click=lambda e: show_popup(add_sub_dialog)
                        ),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text("Aylık Sabit Fatura Yükü", size=12, color=TEXT_MUTED),
                            ft.Text(format_tl(total_sub_cost), size=22, weight=ft.FontWeight.BOLD, color="#F59E0B")
                        ]),
                        ft.Icon(Icons.CALENDAR_MONTH, size=32, color="#F59E0B")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=14,
                    border_radius=12,
                    bgcolor="#1E293B",
                    border=border.all(1, "#334155")
                ),
                
                ft.Text("Takip Edilen Servisler", size=14, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
                ft.ListView(sub_cards, spacing=8, expand=True)
            ], spacing=12, expand=True),
            padding=16,
            expand=True
        )

    # SEKME 3: HESAP BÖLÜŞÜMÜ & ALACAK/VERECEK
    def view_debts():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM receivables ORDER BY is_collected ASC, id DESC")
        rec_list = cur.fetchall()
        conn.close()

        total_receivable = sum([r["amount"] for r in rec_list if not r["is_collected"]])

        def mark_collected(rec_id):
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE receivables SET is_collected = 1 WHERE id = ?", (rec_id,))
            conn.commit()
            conn.close()
            notify("Alacak tahsil edildi olarak işaretlendi! 💰", ACCENT)
            render_current_view()
            page.update()

        cards = []
        for r in rec_list:
            is_done = bool(r["is_collected"])
            cards.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(r["title"], size=14, weight=ft.FontWeight.BOLD, color="white" if not is_done else TEXT_MUTED),
                            ft.Text(f"Kişi: {r['person_name']} • {r['date']}", size=11, color=TEXT_MUTED)
                        ], spacing=4, expand=True),
                        ft.Row([
                            ft.Text(format_tl(r["amount"]), size=14, weight=ft.FontWeight.BOLD, color=ACCENT if not is_done else TEXT_MUTED),
                            ft.IconButton(
                                icon=Icons.CHECK_CIRCLE if is_done else Icons.RADIO_BUTTON_UNCHECKED,
                                icon_color=ACCENT if is_done else "#94A3B8",
                                tooltip="Tahsil Edildi" if is_done else "Tahsil Et",
                                on_click=lambda e, rid=r["id"]: mark_collected(rid) if not is_done else None
                            ),
                            ft.IconButton(
                                icon=Icons.DELETE_OUTLINE,
                                icon_color=TEXT_MUTED,
                                icon_size=18,
                                tooltip="Bu Kaydı Sil",
                                on_click=lambda e, rid=r["id"], rtitle=r["title"]: confirm_action("Kaydı Sil", f"'{rtitle}' alacak kaydını silmek istiyor musunuz?", lambda: delete_single_receivable(rid, rtitle))
                            )
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=12,
                    border_radius=10,
                    bgcolor=CARD_BG if not is_done else "#162032",
                    border=border.all(1, "#334155")
                )
            )

        if not cards:
            cards.append(
                ft.Container(
                    content=ft.Text("Bekleyen alacak kaydı bulunmuyor.", color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    alignment=align.center,
                    padding=40
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Ortak Harcama & Alacak Takibi", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.IconButton(
                        icon=Icons.DELETE_SWEEP,
                        icon_color=DANGER,
                        tooltip="Sadece Alacakları Sıfırla",
                        on_click=lambda e: confirm_action("Alacakları Sıfırla", "Tüm ortak harcama ve alacak kayıtları silinecektir. Emin misiniz?", reset_receivables_data)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text("Bekleyen Toplam Alacağın", size=12, color=TEXT_MUTED),
                            ft.Text(format_tl(total_receivable), size=22, weight=ft.FontWeight.BOLD, color=ACCENT)
                        ]),
                        ft.Icon(Icons.HANDSHAKE, size=32, color=ACCENT)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=14,
                    border_radius=12,
                    bgcolor="#1E293B",
                    border=border.all(1, "#334155")
                ),
                
                ft.Text("Bölüşülen Hesaplar", size=14, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
                ft.ListView(cards, spacing=8, expand=True)
            ], spacing=12, expand=True),
            padding=16,
            expand=True
        )

    # SEKME 4: BİRİKİM HEDEFLERİ
    def view_savings():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM savings_goals ORDER BY id DESC")
        goals = cur.fetchall()
        conn.close()

        def open_deposit(gid):
            active_goal_id["id"] = gid
            show_popup(deposit_goal_dialog)

        goal_cards = []
        for g in goals:
            ratio = min(1.0, g["current_amount"] / g["target_amount"]) if g["target_amount"] > 0 else 0.0
            percent = int(ratio * 100)
            is_completed = percent >= 100

            goal_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon(Icons.SAVINGS, color=ACCENT if is_completed else PRIMARY, size=24),
                                ft.Text(g["title"], size=16, weight=ft.FontWeight.BOLD, color="white")
                            ], spacing=8),
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(f"%{percent}", size=12, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor=ACCENT if is_completed else PRIMARY,
                                    padding=pad.symmetric(horizontal=8, vertical=3),
                                    border_radius=10
                                ),
                                ft.IconButton(
                                    icon=Icons.RESTART_ALT,
                                    icon_color=WARNING,
                                    icon_size=18,
                                    tooltip="Bu Hedefin Birikimini Sıfırla (0 ₺ Yap)",
                                    on_click=lambda e, gid=g["id"], gtitle=g["title"]: confirm_action("Hedef Birikimini Sıfırla", f"'{gtitle}' hedefinde biriken tutarı 0,00 ₺ olarak sıfırlamak istiyor musunuz?", lambda: reset_single_goal_progress(gid, gtitle))
                                ),
                                ft.IconButton(
                                    icon=Icons.DELETE_OUTLINE,
                                    icon_color=DANGER,
                                    icon_size=18,
                                    tooltip="Bu Hedefi Sil",
                                    on_click=lambda e, gid=g["id"], gtitle=g["title"]: confirm_action("Hedefi Sil", f"'{gtitle}' hedefini tamamen silmek istiyor musunuz?", lambda: delete_single_goal(gid, gtitle))
                                ),
                            ], spacing=0)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.ProgressBar(value=ratio, color=ACCENT if is_completed else PRIMARY, bgcolor="#334155"),
                        
                        ft.Row([
                            ft.Text(f"Biriken: {format_tl(g['current_amount'])}", size=12, color=TEXT_MUTED),
                            ft.Text(f"Hedef: {format_tl(g['target_amount'])}", size=12, color=TEXT_MUTED),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        Button(
                            "Hedefe Para Ekle" if not is_completed else "🎉 Tamamlandı!",
                            icon=Icons.ADD if not is_completed else Icons.CHECK,
                            bgcolor="#334155" if not is_completed else "#065F46",
                            color="white",
                            on_click=lambda e, gid=g["id"]: open_deposit(gid) if not is_completed else None
                        )
                    ], spacing=10),
                    padding=16,
                    border_radius=14,
                    bgcolor=CARD_BG,
                    border=border.all(1, "#334155")
                )
            )

        if not goal_cards:
            goal_cards.append(
                ft.Container(
                    content=ft.Text("Henüz birikim hedefi eklenmedi.", color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    alignment=align.center,
                    padding=40
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Birikim Hedeflerim", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Row([
                        ft.IconButton(
                            icon=Icons.DELETE_SWEEP,
                            icon_color=DANGER,
                            tooltip="Tüm Hedefleri Sıfırla",
                            on_click=lambda e: confirm_action("Tüm Hedefleri Sıfırla", "Tüm birikim hedefleriniz silinecektir. Emin misiniz?", reset_goals_data)
                        ),
                        ft.IconButton(
                            icon=Icons.ADD,
                            icon_color=PRIMARY,
                            tooltip="Yeni Hedef Ekle",
                            on_click=lambda e: show_popup(add_goal_dialog)
                        ),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ListView(goal_cards, spacing=10, expand=True)
            ], spacing=12, expand=True),
            padding=16,
            expand=True
        )

    # GÖRÜNÜM YENİLEYİCİ
    def render_current_view():
        if current_tab_index == 0:
            main_content_area.content = view_dashboard()
        elif current_tab_index == 1:
            main_content_area.content = view_transactions()
        elif current_tab_index == 2:
            main_content_area.content = view_subscriptions()
        elif current_tab_index == 3:
            main_content_area.content = view_debts()
        elif current_tab_index == 4:
            main_content_area.content = view_savings()

    def on_navigation_change(e):
        nonlocal current_tab_index
        current_tab_index = e.control.selected_index
        render_current_view()
        page.update()

    # Alt Navigasyon Çubuğu (Bottom Navigation Bar)
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        bgcolor="#0F172A",
        indicator_color=PRIMARY,
        on_change=on_navigation_change,
        destinations=[
            NavDestination(icon=Icons.DASHBOARD_OUTLINED, selected_icon=Icons.DASHBOARD, label="Panel"),
            NavDestination(icon=Icons.RECEIPT_LONG_OUTLINED, selected_icon=Icons.RECEIPT_LONG, label="İşlemler"),
            NavDestination(icon=Icons.CALENDAR_MONTH_OUTLINED, selected_icon=Icons.CALENDAR_MONTH, label="Abonelik"),
            NavDestination(icon=Icons.HANDSHAKE_OUTLINED, selected_icon=Icons.HANDSHAKE, label="Bölüşüm"),
            NavDestination(icon=Icons.SAVINGS_OUTLINED, selected_icon=Icons.SAVINGS, label="Birikim"),
        ]
    )

    render_current_view()
    page.add(main_content_area)

if __name__ == "__main__":
    import sys
    import socket
    import webbrowser

    is_web = "--web" in sys.argv
    if is_web:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "127.0.0.1"
        print("\n" + "="*50)
        print("  🚀 FINANS KOÇU WEB SUNUCUSU BAŞLATILDI!")
        print(f"  📱 Telefonunuzdan (aynı Wi-Fi):")
        print(f"     http://{local_ip}:8550")
        print(f"  💻 Bilgisayardan:")
        print(f"     http://localhost:8550")
        print("="*50 + "\n")
        try:
            webbrowser.open("http://localhost:8550")
        except Exception:
            pass
        
        try:
            import uvicorn
            app_asgi = ft.run(main, export_asgi_app=True)
            uvicorn.run(app_asgi, host="0.0.0.0", port=8550)
        except Exception:
            ft.run(main, host="0.0.0.0", port=8550, view=None)
    else:
        if hasattr(ft, "run"):
            ft.run(main)
        elif hasattr(ft, "app"):
            ft.app(target=main)
        else:
            import flet.app
            flet.app.run(main)
