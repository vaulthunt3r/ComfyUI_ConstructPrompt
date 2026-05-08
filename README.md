# 🏗️ Construct Prompt

A lightweight tag loader for ComfyUI. Inspired by *Eclipse Smart Prompt*, but without the browser overhead and lag. Works instantly even on low-end PCs.

## ✨ Features
- ⚡ **Zero lag** — tags are read only when you press Queue, no preloading into memory
- 📂 **Simple structure** — everything is stored in the `tags/` folder next to the node
- 🎲 **4 modes**: None, Random, Manual, Show tags (multiline)
- 🔁 **Seed control** — stable randomness with a fixed seed
- 🌍 **UTF-8 safe** — works correctly with Cyrillic and emoji

## 📦 Installation
1. Open the `ComfyUI/custom_nodes/` folder
2. Run: `git clone https://github.com/vaulthunt3r/ComfyUI-ConstructPrompt.git`
3. Restart ComfyUI
4. Create a `tags/` folder inside the downloaded folder and add your tags `.txt` files

## 🎛️ Operating Modes

| Mode | Description |
|-------|---------|
| **None** | Empty string |
| **Random** | One random tag from the file |
| **Manual** | Text from the `tag_text` field |
| **Show tags for the selected file (multiline)** | **All file contents line by line** (as is, without comments) |

### 🔍 Multiline Mode — How it Works

Outputs the file line by line, preserving the structure:

**File `example.txt`:**
```txt
# This is a comment — will not be included in the output
masterpiece, best quality
1girl, detailed face
cinematic lighting
