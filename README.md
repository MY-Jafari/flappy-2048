# 🎮 Flappy 2048

A 2D arcade game that combines **Flappy Bird** mechanics with **2048** scoring. Guide a numbered cube through moving columns, merge matching numbers, and reach **2048** to win.

![CI](https://github.com/MY-Jafari/flappy-2048/actions/workflows/ci.yml/badge.svg)

<div align="center">
  <img src="screenshots/start.png" width="230" alt="Start screen with difficulty selector">
  <img src="screenshots/gameplay.png" width="230" alt="Gameplay">
  <img src="screenshots/gameover.png" width="230" alt="Game over screen">
  <img src="screenshots/win.png" width="230" alt="Win screen with confetti">
</div>

---

## 🇮🇷 فارسی

### معرفی

**Flappy 2048** یک بازی دوبعدی است که مکانیک Flappy Bird را با امتیازدهی ۲۰۴۸ ترکیب می‌کند. به‌جای پرنده، یک **مکعب رنگی** را کنترل می‌کنید که عدد فعلی روی آن نمایش داده می‌شود و بازی را با عدد ۲ شروع می‌کند.

با کلیک، لمس یا فشردن کلیدهای `Space`، `↑` و `W` مکعب به سمت بالا می‌پرد. هدف این است که از شکاف ستون‌های متحرک عبور کنید. اگر عدد روی نشانِ داخل شکاف با عدد مکعب برابر باشد، دو عدد مانند بازی ۲۰۴۸ با هم ترکیب می‌شوند؛ برای مثال `۲ + ۲ = ۴`. با رسیدن به عدد **۲۰۴۸** برنده می‌شوید.

بازی با **pygame-ce** ساخته شده است. منطق اصلی بازی، مانند فیزیک، تولید ستون‌ها و ترکیب اعداد، مستقل از pygame نگه داشته شده و pygame فقط در لایه‌ی نمایش و صدا استفاده می‌شود.

### نصب و اجرا

```bash
pip install -r requirements.txt
python main.py
```

### دریافت نسخه‌ی ویندوز

برای اجرای نسخه‌ی ویندوز نیازی به نصب Python نیست. فایل `flappy-2048.exe` را از بخش **Releases** در GitHub دانلود و اجرا کنید.

### ساخت خودکار فایل EXE و انتشار در GitHub

Workflow انتشار با push شدن هر تگ نسخه‌ای که با `v` شروع شود، فایل مستقل ویندوز را می‌سازد و در Release همان تگ قرار می‌دهد:

```bash
git add .
git commit -m "Prepare release"
git push origin main

git tag v1.0.0
git push origin v1.0.0
```

پس از پایان اجرای workflow، فایل `flappy-2048.exe` در صفحه‌ی Release قابل دانلود است. اجرای workflow ممکن است چند دقیقه زمان ببرد؛ نتیجه را می‌توانید در تب **Actions** مشاهده کنید.

### کنترل بازی

| ورودی | عملکرد |
| --- | --- |
| کلیک / لمس / `Space` / `↑` / `W` | پرش |
| `P` | توقف بازی؛ با از دست رفتن فوکوس پنجره نیز بازی خودکار متوقف می‌شود |
| `M` یا دکمه‌ی SOUND | قطع یا وصل کردن صدا |
| `Esc` یا `Q` | خروج |

### سطوح سختی

در صفحه‌ی شروع سه سطح **EASY**، **MEDIUM** و **HARD** وجود دارد. هر سطح سرعت و فاصله‌ی ستون‌ها، اندازه‌ی شکاف و ویژگی‌های فیزیکی مکعب را تغییر می‌دهد. انتخاب آخر شما و بهترین امتیاز هر سطح به‌صورت جداگانه ذخیره می‌شود.

| پارامتر | EASY | MEDIUM | HARD |
| --- | ---: | ---: | ---: |
| اندازه‌ی مکعب | ۵۲px | ۵۶px | ۶۰px |
| جاذبه | ۱۳۰۰ | ۱۵۰۰ | ۱۶۰۰ |
| قدرت پرش | −۵۸۰ | −۵۶۰ | −۵۳۰ |
| ارتفاع پرش تقریبی | ۱۲۹px | ۱۰۴px | ۸۸px |
| اندازه‌ی شکاف | ۲۴۶px | ۲۱۵px | ۱۹۰px |
| سرعت پایه | ۱۱۵ | ۱۴۰ | ۱۷۰ |
| فاصله‌ی ستون‌ها | ۲۸۰px | ۲۵۰px | ۲۴۰px |

**کد مخفی:** هنگام بازی یا توقف، عدد `2048` را با ردیف عددی کیبورد وارد کنید تا مستقیماً به صفحه‌ی برد بروید.

### ساختار پروژه

| فایل | لایه | وظیفه |
| --- | --- | --- |
| `main.py` | اپلیکیشن | نقطه‌ی ورود، حلقه‌ی بازی، ماشین حالت و مدیریت رویدادها |
| `settings.py` | تنظیمات | اندازه‌ی پنجره، فیزیک، رنگ‌ها و سطوح سختی |
| `game_logic.py` | منطق | ترکیب اعداد، تولید ستون‌ها، افزایش سختی و بررسی برخورد |
| `player.py` | منطق | فیزیک مکعب بازیکن و پرش‌ها |
| `obstacle.py` | منطق | ستون‌ها، شکاف‌ها، نشان عددی و برخوردها |
| `storage.py` | منطق | ذخیره‌ی رکوردها، سطح انتخابی و وضعیت صدا |
| `ui.py` | نمایش | رسم مکعب، ستون‌ها، ابرها، کانفتی، HUD و صفحه‌ها |
| `sound.py` | صدا | تولید افکت‌های صوتی بدون فایل صوتی جداگانه |

### تست

```bash
python -m unittest tests.test_logic tests.test_smoke
python main.py --selftest
```

---

## 🇬🇧 English

### Overview

**Flappy 2048** is a 2D arcade game blending **Flappy Bird** mechanics with **2048** scoring. Control a colored cube, fly through gaps in scrolling columns, merge matching numbers, and reach **2048** to win.

The game is built with **pygame-ce**. Its core logic—physics, column generation, number merging, and collision helpers—is independent of pygame, while pygame is used for rendering, input, and sound.

### Install and run

```bash
pip install -r requirements.txt
python main.py
```

### Windows executable

Download `flappy-2048.exe` from the repository’s **Releases** page. Python does not need to be installed to run the executable.

### Automated GitHub Releases

The release workflow runs when a version tag beginning with `v` is pushed. It builds a standalone Windows executable with PyInstaller and uploads it to the GitHub Release for that tag:

```bash
git add .
git commit -m "Prepare release"
git push origin main

git tag v1.0.0
git push origin v1.0.0
```

The executable appears as `flappy-2048.exe` after the workflow finishes. You can monitor the build in the repository’s **Actions** tab.

### Controls

| Input | Action |
| --- | --- |
| Click / tap / `Space` / `↑` / `W` | Jump |
| `P` | Pause; the game also pauses when the window loses focus |
| `M` or the SOUND button | Toggle sound |
| `Esc` or `Q` | Quit |

### Difficulty levels

The start screen offers **EASY**, **MEDIUM**, and **HARD**. Each level changes the column speed and spacing, gap size, and cube physics. The selected level and best score are saved separately for each difficulty.

| Parameter | EASY | MEDIUM | HARD |
| --- | ---: | ---: | ---: |
| Cube size | 52px | 56px | 60px |
| Gravity | 1300 | 1500 | 1600 |
| Jump velocity | −580 | −560 | −530 |
| Approx. jump height | 129px | 104px | 88px |
| Gap height | 246px | 215px | 190px |
| Base speed | 115 | 140 | 170 |
| Column spacing | 280px | 250px | 240px |

**Hidden cheat:** while playing or paused, type `2048` using the number row to jump directly to the win screen.

### Project structure

| File | Layer | Purpose |
| --- | --- | --- |
| `main.py` | app | Entry point, game loop, state machine, and event handling |
| `settings.py` | config | Window, physics, colors, and difficulty settings |
| `game_logic.py` | logic | 2048 merging, column generation, difficulty, and collision helpers |
| `player.py` | logic | Player cube physics and jumping |
| `obstacle.py` | logic | Columns, gaps, number badges, and collision tests |
| `storage.py` | logic | Persistent scores, selected difficulty, and sound state |
| `ui.py` | rendering | Cube, columns, clouds, confetti, HUD, and screens |
| `sound.py` | audio | Synthesized sound effects without audio asset files |

### Tests

```bash
python -m unittest tests.test_logic tests.test_smoke
python main.py --selftest
```
