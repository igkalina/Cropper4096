# Cropper4096

<<<<<<< HEAD
A lightweight GUI tool that randomly crops large images to **4096×2304 px** and saves them as compressed JPEG files (≤1 MB).  
Built with **Python + Tkinter + Pillow**, packaged into a standalone `.exe` with PyInstaller.
=======
A lightweight desktop tool that randomly crops large images to **4096×2304 px** and automatically compresses them to **≤1 MB JPEGs**.  
Built with **Python + Tkinter + Pillow**, packaged into a standalone `.exe` via **PyInstaller**.

---

## ✨ Features
<<<<<<< HEAD
- Randomly selects an image from a chosen input folder  
- Random crop of 4096×2304 px, scaled if smaller  
- Auto compression to ≤1 MB (quality adjusted dynamically)  
- Clean graphical interface (choose folders and click “Crop”)  
- Saves results as `*_crop.jpg`  
- Remembers your last used folders between runs  
- Optional PowerShell script for local **code signing** (no warnings on Windows)
=======
- Randomly selects an image from a chosen folder  
- Performs a random crop of **4096×2304 px**  
- Scales up smaller images proportionally before cropping  
- Automatically adjusts JPEG quality to keep file size under 1 MB  
- Clean and simple graphical interface (choose folders → click **Crop**)  
- Saves output as `*_crop.jpg` (no overwriting — adds `_1`, `_2`, etc.)  
- Remembers your last used folders between sessions  
- Includes optional PowerShell script to locally sign `.exe` files on Windows

---

## 🧰 Requirements
- **Python 3.10+**
<<<<<<< HEAD
- Libraries:  
  ```bash
  pip install pillow
=======
- Library:
  ```bash
  pip install pillow
  ```

---

## 🚀 Run from source
```bash
python crop_gui.py
```
or simply double-click the prebuilt `Cropper4096.exe` (no console window).

---

## 🪟 GUI usage
1. Click **Browse…** to select:
   - **Source folder** – where your original images are
   - **Destination folder** – where cropped images will be saved
2. Click **Crop**  
   → One random image will be cropped to 4096×2304 px and saved as `*_crop.jpg`
3. Click **Open output folder** to view results

The tool automatically remembers the last folders you used.

---

## 🏗️ Build as EXE
```bash
pyinstaller --onefile --windowed --name "Cropper4096" crop_gui.py
```

After building:
```
dist/
└── Cropper4096.exe
```

> Typical file size: 50–100 MB (includes Python and Tk/Tcl runtime).

---

## 🔏 Optional: Local code-signing (Windows)

To reduce SmartScreen or antivirus warnings on **your PC**,  
you can locally sign the `.exe` with a self-signed certificate using the provided PowerShell script:

```powershell
powershell -ExecutionPolicy Bypass -File "sign\sign.ps1"
```

This script:
- Creates a self-signed “Cropper4096 Developer” certificate  
- Adds it to your user’s trusted stores  
- Signs all `.exe` files inside the `dist` folder  

Check the signature:
```powershell
Get-AuthenticodeSignature ".\dist\Cropper4096.exe" | fl Status,StatusMessage
```
You should see `Status : Valid`.

> On other computers, the certificate must be installed into *Trusted Publisher* and *Root* stores  
> or replaced with a paid code-signing certificate (e.g., Comodo, Sectigo, DigiCert).

---

## 🗂️ Project structure
```
Cropper4096/
├─ crop_gui.py        # main GUI logic (Tkinter + Pillow)
├─ README.md          # this file
├─ sign/
│  └─ sign.ps1        # optional PowerShell signing script
└─ .gitignore         # recommended ignores for build/output files
```

Example `.gitignore`:
```
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.egg-info/
.venv/
venv/
.vscode/
.idea/
build/
dist/
*.spec
*.log
.DS_Store
Thumbs.db
```
