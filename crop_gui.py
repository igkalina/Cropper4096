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
    if os.name == "nt" and os.getenv("APPDATA"):
        base = Path(os.getenv("APPDATA")) / "Cropper4096"
        base.mkdir(parents=True, exist_ok=True)
        return base / "config.json"
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

def process_one_random(input_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    src = pick_random_image(input_dir)
    img = load_image_fix_orientation(src)
    img = ensure_min_size_cover(img, TARGET_W, TARGET_H)
    img = random_crop(img, TARGET_W, TARGET_H)
    out_name = f"{src.stem}{OUTPUT_SUFFIX}.jpg"
    out_path = non_clobber_path(output_dir / out_name)
    try_save_jpeg_under_1mb(img, out_path)
    return src, out_path

def process_one_selected(file_path: Path, output_dir: Path) -> Path:
    if not file_path.is_file():
        raise FileNotFoundError("Выбранный файл не существует.")
    if file_path.suffix.lower() not in EXTS:
        raise ValueError("Выбранный файл не является поддерживаемым изображением.")
    img = load_image_fix_orientation(file_path)
    img = ensure_min_size_cover(img, TARGET_W, TARGET_H)
    img = random_crop(img, TARGET_W, TARGET_H)
    out_name = f"{file_path.stem}{OUTPUT_SUFFIX}.jpg"
    out_path = non_clobber_path(output_dir / out_name)
    try_save_jpeg_under_1mb(img, out_path)
    return out_path

# ---------- GUI ----------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Случайный кроп 4096×2304 → JPEG ≤ 1 МБ")
        self.geometry("760x360")
        self.resizable(False, False)

        cfg = load_config()
        # вкладка 1 (папки)
        self.input_var = tk.StringVar(value=cfg.get("input_dir", ""))
        self.output_var = tk.StringVar(value=cfg.get("output_dir", ""))
        self.delete_src_var = tk.BooleanVar(value=cfg.get("delete_after", False))
        # вкладка 2 (один файл)
        self.file_var = tk.StringVar(value=cfg.get("single_file", ""))
        self.output2_var = tk.StringVar(value=cfg.get("output_dir2", cfg.get("output_dir", "")))

        self.status_var = tk.StringVar(value="Выберите папки/файл и нажмите «Кадрировать»")

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        pad = {"padx": 12, "pady": 8}

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # ---- TAB 1: Random from folder ----
        tab1 = ttk.Frame(nb)
        nb.add(tab1, text="Случайный из папки")

        frm_in = ttk.Frame(tab1); frm_in.pack(fill="x", **pad)
        ttk.Label(frm_in, text="Папка с изображениями:").pack(anchor="w")
        row_in = ttk.Frame(frm_in); row_in.pack(fill="x", pady=(4, 0))
        ttk.Entry(row_in, textvariable=self.input_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row_in, text="Обзор…", command=self.browse_input).pack(side="left", padx=(8, 0))

        frm_out = ttk.Frame(tab1); frm_out.pack(fill="x", **pad)
        ttk.Label(frm_out, text="Папка для сохранения:").pack(anchor="w")
        row_out = ttk.Frame(frm_out); row_out.pack(fill="x", pady=(4, 0))
        ttk.Entry(row_out, textvariable=self.output_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row_out, text="Обзор…", command=self.browse_output).pack(side="left", padx=(8, 0))

        # delete checkbox
        frm_opts = ttk.Frame(tab1); frm_opts.pack(fill="x", **pad)
        ttk.Checkbutton(frm_opts, text="Удалять исходный файл после кадрирования (без корзины)",
                        variable=self.delete_src_var, command=self.save_current_paths).pack(anchor="w")

        # buttons
        frm_btn = ttk.Frame(tab1); frm_btn.pack(fill="x", **pad)
        self.btn_go1 = ttk.Button(frm_btn, text="Кадрировать", command=self.on_crop_random, style="Accent.TButton")
        self.btn_go1.pack(side="left", padx=(0, 8))
        ttk.Button(frm_btn, text="Открыть папку сохранения", command=self.open_output_dir1).pack(side="left")

        # ---- TAB 2: Select single file ----
        tab2 = ttk.Frame(nb)
        nb.add(tab2, text="Выборочный файл")

        frm_file = ttk.Frame(tab2); frm_file.pack(fill="x", **pad)
        ttk.Label(frm_file, text="Файл изображения:").pack(anchor="w")
        row_file = ttk.Frame(frm_file); row_file.pack(fill="x", pady=(4, 0))
        ttk.Entry(row_file, textvariable=self.file_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row_file, text="Выбрать файл…", command=self.browse_file).pack(side="left", padx=(8, 0))

        frm_out2 = ttk.Frame(tab2); frm_out2.pack(fill="x", **pad)
        ttk.Label(frm_out2, text="Папка для сохранения:").pack(anchor="w")
        row_out2 = ttk.Frame(frm_out2); row_out2.pack(fill="x", pady=(4, 0))
        ttk.Entry(row_out2, textvariable=self.output2_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row_out2, text="Обзор…", command=self.browse_output2).pack(side="left", padx=(8, 0))

        frm_btn2 = ttk.Frame(tab2); frm_btn2.pack(fill="x", **pad)
        self.btn_go2 = ttk.Button(frm_btn2, text="Кадрировать выбранный", command=self.on_crop_selected, style="Accent.TButton")
        self.btn_go2.pack(side="left", padx=(0, 8))
        ttk.Button(frm_btn2, text="Открыть папку сохранения", command=self.open_output_dir2).pack(side="left")

        # status
        frm_status = ttk.Frame(self); frm_status.pack(fill="x", **pad)
        ttk.Label(frm_status, textvariable=self.status_var, foreground="#444").pack(anchor="w")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ----- browse helpers -----
    def browse_input(self):
        d = filedialog.askdirectory(title="Выберите папку с изображениями")
        if d:
            self.input_var.set(d); self.save_current_paths()

    def browse_output(self):
        d = filedialog.askdirectory(title="Выберите папку для сохранения")
        if d:
            self.output_var.set(d); self.save_current_paths()

    def browse_file(self):
        ftypes = [("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"),
                  ("All files", "*.*")]
        f = filedialog.askopenfilename(title="Выберите файл изображения", filetypes=ftypes)
        if f:
            self.file_var.set(f); self.save_current_paths()

    def browse_output2(self):
        d = filedialog.askdirectory(title="Выберите папку для сохранения")
        if d:
            self.output2_var.set(d); self.save_current_paths()

    # ----- actions -----
    def on_crop_random(self):
        in_dir = Path(self.input_var.get().strip() or "")
        out_dir = Path(self.output_var.get().strip() or "")
        delete_src = self.delete_src_var.get()

        if not in_dir.is_dir():
            messagebox.showerror("Ошибка", "Укажите корректную папку с изображениями.")
            return
        if not out_dir.is_dir():
            messagebox.showerror("Ошибка", "Укажите корректную папку для сохранения.")
            return

        self.btn_go1.state(["disabled"])
        self.status_var.set("Обработка…")
        self.save_current_paths()

        try:
            src, out_path = process_one_random(in_dir, out_dir)
            # удаление исходника, если отмечено
            if delete_src:
                try:
                    os.remove(src)
                    deleted_note = " (исходник удалён)"
                except Exception as e:
                    deleted_note = f" (не удалось удалить исходник: {e})"
            else:
                deleted_note = ""
            self.status_var.set(f"Готово: {out_path.name} (из {src.name}){deleted_note}")
            try:
                size = out_path.stat().st_size
            except Exception:
                size = "?"
            messagebox.showinfo("Готово", f"Сохранено:\n{out_path}\nРазмер: {size} байт{deleted_note}")
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
            self.btn_go1.state(["!disabled"])

    def on_crop_selected(self):
        file_path = Path(self.file_var.get().strip() or "")
        out_dir = Path(self.output2_var.get().strip() or "")

        if not file_path.is_file():
            messagebox.showerror("Ошибка", "Укажите корректный файл изображения.")
            return
        if not out_dir.is_dir():
            messagebox.showerror("Ошибка", "Укажите корректную папку для сохранения.")
            return

        self.btn_go2.state(["disabled"])
        self.status_var.set("Обработка выбранного файла…")
        self.save_current_paths()

        try:
            out_path = process_one_selected(file_path, out_dir)
            self.status_var.set(f"Готово: {out_path.name} (из {file_path.name})")
            try:
                size = out_path.stat().st_size
            except Exception:
                size = "?"
            messagebox.showinfo("Готово", f"Сохранено:\n{out_path}\nРазмер: {size} байт")
        except (FileNotFoundError, ValueError) as e:
            messagebox.showwarning("Ошибка выбора", str(e))
            self.status_var.set("Ошибка выбора файла.")
        except RuntimeError as e:
            messagebox.showerror("Не удалось уложиться в 1 МБ", str(e))
            self.status_var.set("Не удалось сохранить ≤ 1 МБ. Попробуйте другой файл.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Непредвиденная ошибка:\n{e}")
            self.status_var.set("Ошибка при обработке выбранного файла.")
        finally:
            self.btn_go2.state(["!disabled"])

    # ----- misc -----
    def open_output_dir1(self):
        self._open_dir(self.output_var.get().strip())

    def open_output_dir2(self):
        self._open_dir(self.output2_var.get().strip())

    def _open_dir(self, path: str):
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

    def save_current_paths(self):
        save_config({
            "input_dir": self.input_var.get().strip(),
            "output_dir": self.output_var.get().strip(),
            "delete_after": bool(self.delete_src_var.get()),
            "single_file": self.file_var.get().strip(),
            "output_dir2": self.output2_var.get().strip()
        })

    def on_close(self):
        self.save_current_paths()
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
