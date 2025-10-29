#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import random
from io import BytesIO
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageOps

TARGET_W, TARGET_H = 4096, 2304
MAX_BYTES = 1_000_000
OUTPUT_SUFFIX = "_crop"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

# ----------------- КОНФИГ -----------------

def get_config_path() -> Path:
    # Windows: %APPDATA%\Cropper4096\config.json
    if os.name == "nt" and os.getenv("APPDATA"):
        base = Path(os.getenv("APPDATA")) / "Cropper4096"
    else:
        # Linux/macOS: ~/.cropper4096.json (в корне home или подпапка)
        base = Path.home()
    if base.is_dir():
        base.mkdir(parents=True, exist_ok=True)
        return base / ("config.json" if base.name == "Cropper4096" else ".cropper4096.json")
    # fallback
    return Path.home() / ".cropper4096.json"

CONFIG_PATH = get_config_path()

def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}

def save_config(data: dict) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # не ломаем работу GUI, если вдруг прав нет
        pass

# ---------- ЛОГИКА ОБРАБОТКИ ИЗОБРАЖЕНИЯ ----------

def pick_random_image(folder: Path) -> Path:
    imgs = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTS and OUTPUT_SUFFIX not in p.stem]
    if not imgs:
        raise FileNotFoundError("В папке нет подходящих изображений.")
    return random.choice(imgs)

def load_image_fix_orientation(path: Path) -> Image.Image:
    img = Image.open(path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    return img.convert("RGB")

def ensure_min_size_cover(img: Image.Image, tw: int, th: int) -> Image.Image:
    w, h = img.size
    scale = max(tw / w, th / h)
    if scale > 1.0:
        img = img.resize((int(round(w * scale)), int(round(h * scale))), Image.LANCZOS)
    return img

def random_crop(img: Image.Image, tw: int, th: int) -> Image.Image:
    w, h = img.size
    if w < tw or h < th:
        img = ensure_min_size_cover(img, tw, th)
        w, h = img.size
    x0 = random.randint(0, max(0, w - tw))
    y0 = random.randint(0, max(0, h - th))
    return img.crop((x0, y0, x0 + tw, y0 + th))

def save_under_limit(img: Image.Image, out_path: Path, max_bytes: int, q_min: int, q_max: int) -> bool:
    low, high = q_min, q_max
    best_buf = None
    while low <= high:
        q = (low + high) // 2
        buf = BytesIO()
        try:
            img.save(buf, format="JPEG", quality=q, optimize=True, progressive=True, subsampling="4:2:0")
        except OSError:
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=q)
        size = buf.tell()
        if size <= max_bytes:
            best_buf = buf
            low = q + 1
        else:
            high = q - 1
    if best_buf is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(best_buf.getbuffer())
        best_buf.close()
        return True
    return False

def try_save_jpeg_under_1mb(img: Image.Image, out_path: Path) -> None:
    if not save_under_limit(img, out_path, MAX_BYTES, q_min=40, q_max=95):
        if not save_under_limit(img, out_path, MAX_BYTES, q_min=10, q_max=39):
            raise RuntimeError("Не удалось уложиться в 1 МБ даже при низком качестве.")

def non_clobber_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path
    stem, suffix = base_path.stem, base_path.suffix
    i = 1
    while True:
        cand = base_path.with_name(f"{stem}_{i}{suffix}")
        if not cand.exists():
            return cand
        i += 1

def process_one(input_dir: Path, output_dir: Path) -> Path:
    src = pick_random_image(input_dir)
    img = load_image_fix_orientation(src)
    img = ensure_min_size_cover(img, TARGET_W, TARGET_H)
    img = random_crop(img, TARGET_W, TARGET_H)
    out_name = f"{src.stem}{OUTPUT_SUFFIX}.jpg"
    out_path = non_clobber_path(output_dir / out_name)
    try_save_jpeg_under_1mb(img, out_path)
    return src, out_path

# ---------- GUI ----------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Случайный кроп 4096×2304 → JPEG ≤ 1 МБ")
        self.geometry("700x260")
        self.resizable(False, False)

        cfg = load_config()
        self.input_var = tk.StringVar(value=cfg.get("input_dir", ""))
        self.output_var = tk.StringVar(value=cfg.get("output_dir", ""))
        self.status_var = tk.StringVar(value="Выберите папки и нажмите «Кадрировать»")

        pad = {"padx": 12, "pady": 8}

        # Входная папка
        frm_in = ttk.Frame(self)
        frm_in.pack(fill="x", **pad)
        ttk.Label(frm_in, text="Папка с изображениями:").pack(anchor="w")
        row_in = ttk.Frame(frm_in)
        row_in.pack(fill="x", pady=(4, 0))
        self.ent_in = ttk.Entry(row_in, textvariable=self.input_var)
        self.ent_in.pack(side="left", fill="x", expand=True)
        ttk.Button(row_in, text="Обзор…", command=self.browse_input).pack(side="left", padx=(8, 0))

        # Выходная папка
        frm_out = ttk.Frame(self)
        frm_out.pack(fill="x", **pad)
        ttk.Label(frm_out, text="Папка для сохранения:").pack(anchor="w")
        row_out = ttk.Frame(frm_out)
        row_out.pack(fill="x", pady=(4, 0))
        self.ent_out = ttk.Entry(row_out, textvariable=self.output_var)
        self.ent_out.pack(side="left", fill="x", expand=True)
        ttk.Button(row_out, text="Обзор…", command=self.browse_output).pack(side="left", padx=(8, 0))

        # Кнопки
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill="x", **pad)
        self.btn_go = ttk.Button(frm_btn, text="Кадрировать", command=self.on_crop, style="Accent.TButton")
        self.btn_go.pack(side="left", padx=(0, 8))
        ttk.Button(frm_btn, text="Открыть папку сохранения", command=self.open_output_dir).pack(side="left")

        # Статус
        frm_status = ttk.Frame(self)
        frm_status.pack(fill="x", **pad)
        ttk.Label(frm_status, textvariable=self.status_var, foreground="#444").pack(anchor="w")

        # Тема
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        # Корректное сохранение конфига при закрытии
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def browse_input(self):
        d = filedialog.askdirectory(title="Выберите папку с изображениями")
        if d:
            self.input_var.set(d)
            self.save_current_paths()

    def browse_output(self):
        d = filedialog.askdirectory(title="Выберите папку для сохранения")
        if d:
            self.output_var.set(d)
            self.save_current_paths()

    def save_current_paths(self):
        save_config({
            "input_dir": self.input_var.get().strip(),
            "output_dir": self.output_var.get().strip()
        })

    def on_crop(self):
        in_dir = Path(self.input_var.get().strip() or "")
        out_dir = Path(self.output_var.get().strip() or "")

        if not in_dir.is_dir():
            messagebox.showerror("Ошибка", "Укажите корректную папку с изображениями.")
            return
        if not out_dir.is_dir():
            messagebox.showerror("Ошибка", "Укажите корректную папку для сохранения.")
            return

        # сохраняем выбранные пути сразу, чтобы не потерять при падении
        self.save_current_paths()

        self.btn_go.state(["disabled"])
        self.status_var.set("Обработка…")

        try:
            src, out_path = process_one(in_dir, out_dir)
            self.status_var.set(f"Готово: {out_path.name} (из {src.name})")
            try:
                size = out_path.stat().st_size
            except Exception:
                size = "?"
            messagebox.showinfo("Готово", f"Сохранено:\n{out_path}\nРазмер: {size} байт")
        except FileNotFoundError as e:
            messagebox.showwarning("Нет изображений", str(e))
            self.status_var.set("В выбранной входной папке не найдено изображений.")
        except RuntimeError as e:
            messagebox.showerror("Не удалось уложиться в 1 МБ", str(e))
            self.status_var.set("Не удалось сохранить ≤ 1 МБ. Попробуйте другое изображение.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Непредвиденная ошибка:\n{e}")
            self.status_var.set("Ошибка при обработке.")
        finally:
            self.btn_go.state(["!disabled"])

    def open_output_dir(self):
        path = self.output_var.get().strip()
        if not path:
            messagebox.showinfo("Папка не указана", "Сначала выберите папку для сохранения.")
            return
        p = Path(path)
        if not p.is_dir():
            messagebox.showerror("Ошибка", "Указанная папка для сохранения не существует.")
            return
        try:
            if os.name == "nt":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                import subprocess; subprocess.Popen(["open", str(p)])
            else:
                import subprocess; subprocess.Popen(["xdg-open", str(p)])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")

    def on_close(self):
        # финально сохраняем то, что в полях
        self.save_current_paths()
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
