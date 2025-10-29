# Cropper4096

A lightweight GUI tool that randomly crops large images to **4096×2304 px** and saves them as compressed JPEG files (≤1 MB).  
Built with **Python + Tkinter + Pillow**, packaged into a standalone `.exe` with PyInstaller.

---

## ✨ Features
- Randomly selects an image from a chosen input folder  
- Random crop of 4096×2304 px, scaled if smaller  
- Auto compression to ≤1 MB (quality adjusted dynamically)  
- Clean graphical interface (choose folders and click “Crop”)  
- Saves results as `*_crop.jpg`  
- Remembers your last used folders between runs  
- Optional PowerShell script for local **code signing** (no warnings on Windows)

---

## 🧰 Requirements
- **Python 3.10+**
- Libraries:  
  ```bash
  pip install pillow
