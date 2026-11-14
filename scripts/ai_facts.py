"""Facts for the "Ask your AI" prompts on tool pages (see ai_prompts in build_site.py).

Each tool has:
- facts: what an AI needs to explain the tool and guide someone through it. Plain words, no guessing:
  the prompt tells the AI to use only these. The official download and page links are added for you.
- agent_steps (Windows apps only): what an AI agent may do on the PC to set it up, step by step.
- agent_rules (optional): extra rules for the agent, on top of the shared safety rules.

Memory and CPU figures were measured on a real Windows 11 PC in November 2026, with each app running
normally (Task Manager shows the larger "working set" number). Browser tools have no measured
figures, so their prompts say so instead of letting the AI guess.
"""

UNSIGNED = ("Windows may show \"Windows protected your PC\" because the app isn't code-signed: click More "
            "info, then Run anyway. Windows shows this for small apps from independent makers.")
UAC = "When it first starts, Windows asks whether the app may make changes: click Yes."
CHROME_MEMORY = ("Resource use: no measured figures. It's a small extension; if asked, say so and suggest "
                 "checking Chrome's own Task Manager (Shift + Esc) instead of guessing.")


def chrome_setup(name, file, folder):
    return (f"How to add it (it isn't in the Chrome Web Store yet): download {file}, right-click it and choose "
            f"Extract All, then Extract, which gives a folder called {folder}. Move that folder somewhere it can "
            "stay, like Documents, because Chrome uses it every time. Open chrome://extensions, switch on "
            f"Developer mode at the top right, click Load unpacked and choose the {folder} folder. In Edge use "
            "edge://extensions (Developer mode is in the menu on the left); in Brave use brave://extensions.")


def chrome_remove(name, folder):
    return (f"To update: download it again, unzip it into the same {folder} folder, then click the reload "
            f"arrow on {name} in chrome://extensions. To remove: click Remove on {name} in "
            f"chrome://extensions, then delete the {folder} folder.")


def windows_agent_steps(name, exe, extra_first_run=(), extra_after=()):
    """The usual set-up for one of the small Windows apps."""
    return [
        "Check that this PC runs Windows 10 or 11.",
        f"Create the folder %LOCALAPPDATA%\\Programs\\{name} and download {exe} into it.",
        *extra_first_run,
        f"Start {exe}. If Windows shows \"Windows protected your PC\", tell me to click More info, then Run "
        "anyway. If Windows asks whether the app may make changes, tell me to click Yes.",
        *extra_after,
        f"Ask whether {name} should start with Windows. If yes, tell me to right-click its icon by the clock and "
        "tick Start with Windows. Use the app's own option; don't add startup entries yourself.",
        f"Finish with a short summary: where the file is, how to use {name}, and how to remove it.",
    ]


AI_FACTS = {
    "quicknotes": {
        "facts": [
            "What it does: copies text from anything on the screen (photos, videos, PDFs, apps) in any language, "
            "including Bangla, English and Hindi. Double-tap Right Alt, drag a box over the text, and it's copied "
            "to the clipboard. The shortcut can be changed to another key or a key combination.",
            "How it reads text: it sends only the selected area to Google Gemini. It needs a free Gemini API key "
            "from Google AI Studio, set up once in about a minute in a setup window that opens by itself.",
            "Privacy: nothing is saved to disk. On Google's free plan, Google may use what is sent to improve its "
            "products, so don't scan passwords, bank details or other private information.",
            "Works on: Windows 10 and 11. One file, QuickNotes.exe (1.3 MB). Nothing to install. Free and open "
            "source (MIT licence).",
            "Resource use (measured): about 6.5 MB of memory (28 MB shown in Task Manager) and 0% CPU while it "
            "waits. A scan takes about 2 seconds and needs the internet.",
            UNSIGNED,
            "Settings and the encrypted key are kept in %AppData%\\QuickNotes.",
            "Menu by the clock (right-click the scan icon): Scan text on screen, How to use, Change shortcut, "
            "Pause, Start with Windows, Sound when copied, Change Gemini API key, Exit.",
            "To remove it: untick Start with Windows, click Exit, then delete QuickNotes.exe and the "
            "%AppData%\\QuickNotes folder.",
        ],
        "agent_rules": ["Never ask for, read or store my Gemini API key. I'll paste it into QuickNotes myself."],
        "agent_steps": windows_agent_steps(
            "QuickNotes", "QuickNotes.exe",
            extra_after=["Tell me to finish the setup window myself: Open AI Studio, Create API key, Copy, then "
                         "Test and Save."]),
    },
    "deskwidget": {
        "facts": [
            "What it does: puts good-looking widgets on the Windows desktop, under your windows: Analog Clock, "
            "World Times (2 to 5 cities), Calendar, At a Glance (weather, date, sunrise or sunset and a world "
            "clock), Control Panel (Wi-Fi, Bluetooth, brightness, volume, microphone mute, speaker and microphone), "
            "Photo Card, Focus Timer (15 to 60 minutes), a daily Quote and a Custom Quote.",
            "Looks: every widget can be Dark, Light or Vibrant (your wallpaper softly blurred behind it). Drag a "
            "widget to move it, drag a corner to resize it, right-click it for Appearance, Size, Opacity, Lock "
            "Position, Lock Menu and Remove Widget.",
            "How to use: open the Desk Widgets window (Start menu, the icon by the clock, or the exe again), then "
            "drag a widget onto the desktop or double-click it. Closing the window keeps the widgets running. "
            "Settings in the app: Start with Windows, High Priority, OLED Pixel Shift, Locked Widgets, light or "
            "dark look.",
            "Works on: Windows 10 and 11. One file, DeskWidgets.exe (0.2 MB). Nothing to install; it adds itself "
            "to the Start menu on first run. A portable version (DeskWidgets-Portable.zip) keeps its settings in "
            "its own folder, handy for a USB stick. Free and open source (MIT licence).",
            "Resource use (measured): about 80 to 130 MB of memory, depending on how many widgets and photos are "
            "open, and almost no CPU (0.04%) while idle. Drawing pauses while the PC is locked.",
            "Privacy: no account, no tracking, no ads. Only the weather in At a Glance goes online: the city is "
            "looked up once with the free Open-Meteo service, then only its map position is sent every 15 minutes.",
            UNSIGNED,
            "Settings and photo copies are kept in %AppData%\\DeskWidgets.",
            "To remove it: switch off Start with Windows in the app's Settings, quit it from the icon by the clock, "
            "then delete DeskWidgets.exe and the %AppData%\\DeskWidgets folder.",
            "Checksums: each release has a SHA256SUMS.txt file next to the download, at "
            "https://github.com/mogdho/deskwidget/releases/latest/download/SHA256SUMS.txt",
        ],
        "agent_steps": [
            "Check that this PC runs Windows 10 or 11.",
            "Create the folder %LOCALAPPDATA%\\Programs\\Desk Widgets and download DeskWidgets.exe and "
            "SHA256SUMS.txt into it.",
            "Check that the SHA-256 hash of DeskWidgets.exe matches the line for it in SHA256SUMS.txt. If it "
            "doesn't match, stop and tell me.",
            "Start DeskWidgets.exe. If Windows shows \"Windows protected your PC\", tell me to click More info, "
            "then Run anyway.",
            "Ask which widgets I'd like (for example World Times, At a Glance or Control Panel), then tell me how "
            "to drag them onto the desktop from the Desk Widgets window. You can't place them for me.",
            "Ask whether Desk Widgets should start with Windows. If yes, tell me to open Settings in the app and "
            "switch on Start with Windows. Use the app's own option; don't add startup entries yourself.",
            "Finish with a short summary: where the file is, how to add or remove widgets, and how to remove "
            "the app.",
        ],
    },
    "alwaysnumlock": {
        "facts": [
            "What it does: keeps Num Lock switched on, so the number pad always types numbers: after an accidental "
            "press, after sleep, after the lock screen, and (if chosen) at the Windows sign-in screen for number "
            "PINs.",
            "Works on: Windows 10 and 11. One file, AlwaysNumLock.exe (1.3 MB). Nothing to install. Free and open "
            "source.",
            "Resource use (measured): about 3.7 MB of memory (10.5 MB shown in Task Manager) and almost no CPU "
            "(0.01%).",
            UNSIGNED,
            UAC,
            "First run: it asks whether Num Lock should also be on at the Windows sign-in screen. Yes is useful "
            "for people who sign in with a number PIN.",
            "Menu by the clock (right-click the 1-2-3 icon): Pause (turn Num Lock off for a while, for example in "
            "a game; double-clicking the icon does the same), Start with Windows, Num Lock on at sign-in screen, "
            "Exit.",
            "Settings: a small settings file with the same name, next to AlwaysNumLock.exe.",
            "To remove it: untick Start with Windows (and Num Lock on at sign-in screen if wanted), click Exit, "
            "then delete AlwaysNumLock.exe and the settings file next to it.",
        ],
        "agent_steps": windows_agent_steps(
            "AlwaysNumLock", "AlwaysNumLock.exe",
            extra_after=["When it asks whether Num Lock should be on at the sign-in screen, explain the choice and "
                         "let me answer it myself."]),
    },
    "capslock-copypaste": {
        "facts": [
            "What it does: turns Caps Lock into copy and paste. Tap Caps Lock once to copy what's selected, twice "
            "quickly to paste. Ctrl + Caps Lock twice pastes as plain text (no fonts, colours or links). "
            "Shift + Caps Lock turns real CAPITALS on or off. Works with text, pictures and files in every app.",
            "Feedback: a small note next to the mouse says Copied! or Pasted!. If nothing was selected it says "
            "Nothing copied! and keeps the clipboard as it was.",
            "Works on: Windows 10 and 11. One file, Capslock-CopyPaste.exe (1.3 MB). Nothing to install. Free and "
            "open source.",
            "Resource use (measured): about 4.1 MB of memory (12.2 MB shown in Task Manager) and 0% CPU while it "
            "waits.",
            UNSIGNED,
            UAC + " This lets it work in every app, including Task Manager.",
            "Menu by the clock (right-click the up-arrow icon): Pause (Caps Lock works normally until clicked "
            "again; double-clicking the icon does the same), Start with Windows, Exit.",
            "Troubleshooting: if tapping twice copies instead of pasting, tap a little faster. If nothing happens, "
            "check the icon is there and not faded (paused).",
            "To remove it: untick Start with Windows, click Exit, then delete Capslock-CopyPaste.exe.",
        ],
        "agent_steps": windows_agent_steps("Capslock-CopyPaste", "Capslock-CopyPaste.exe"),
    },
    "copilot2gemini": {
        "facts": [
            "What it does: makes the Copilot key on Windows laptops open Google Gemini (or ChatGPT, Claude or any "
            "assistant installed as a web app) in its own window. Press once to open it, again to hide it, and it "
            "brings it to the front if it's behind other windows. Ctrl + Copilot opens a second window. Without a "
            "Copilot key, Win + C does the same.",
            "Before it: install Gemini as an app. In Chrome, Edge or Brave open gemini.google.com, click the "
            "three-dot menu, then Save and share (or Apps), then Install page as app, and click Install. Without "
            "this it still works, but opens Gemini in a normal browser tab.",
            "Works on: Windows 10 and 11. One file, Copilot2Gemini.exe (1.3 MB). Nothing to install. Free and open "
            "source.",
            "Resource use (measured): about 5.3 MB of memory (19.6 MB shown in Task Manager) and 0% CPU while it "
            "waits.",
            UNSIGNED,
            UAC + " On first run a message says Found Google Gemini.",
            "Other assistants: install chatgpt.com or claude.ai as an app the same way, then right-click the "
            "Copilot2Gemini icon, choose Assistant, then Rescan installed apps, and pick it from the list.",
            "Menu by the clock: Assistant (pick the web app the key opens), Pause, Start with Windows, Exit.",
            "Settings: a small settings file with the same name, next to Copilot2Gemini.exe.",
            "To remove it: untick Start with Windows, click Exit, then delete Copilot2Gemini.exe and the settings "
            "file next to it.",
        ],
        "agent_steps": windows_agent_steps(
            "Copilot2Gemini", "Copilot2Gemini.exe",
            extra_first_run=["Ask which assistant I want (Gemini, ChatGPT or Claude) and whether it's installed as "
                             "an app in Chrome, Edge or Brave. If not, tell me how to install it as an app; you "
                             "can't click Install for me."]),
    },
    "nn-tab": {
        "facts": [
            "What it does: replaces Chrome's new tab page with a calm one: a big clock and date, bookmark tiles "
            "(drag to reorder, sort into groups, right-click to edit), a short notes list, your own quote, a dark "
            "or light theme with any wallpaper, and a button that opens ChatGPT in a small window.",
            "Works in: Chrome, Edge and Brave on a computer. One file, NN-tab.zip (1.9 MB). Free and open source.",
            chrome_setup("NN-tab", "NN-tab.zip", "NN-tab"),
            "Settings: click the NN-tab icon in the toolbar (pin it from the puzzle-piece icon if it's hidden): "
            "Theme, Wallpaper, Sharper icons (looks up clearer icons online, off at first), and Backup to a file.",
            "Privacy: bookmarks, notes and settings stay on the computer. No account and no tracking.",
            CHROME_MEMORY,
            chrome_remove("NN-tab", "NN-tab"),
        ],
    },
    "ytmodify": {
        "facts": [
            "What it does: makes YouTube nicer to watch. Ambient light (a soft glow around the video that follows "
            "its colours, and it can hide black bars), auto pop-out (a playing video floats in a small window when "
            "you switch tabs), a chosen quality for each view (for example 1080p in full screen), and a nicer look "
            "with a bigger player and hover colours.",
            "Works in: Chrome, Edge and Brave on a computer. One file, ytModify.zip (0.9 MB). Free and open "
            "source. It isn't made by Google.",
            chrome_setup("ytModify", "ytModify.zip", "ytModify"),
            "Settings: click the ytModify icon in the toolbar (pin it from the puzzle-piece icon if it's hidden). "
            "Four tabs: PiP, Look, Quality and Ambient. Changes show straight away.",
            "Keys while watching: P pops the video out or back in, G turns the glow on or off, B and V hide black "
            "bars, H stretches the video into that space. Switching to another app rather than a tab? Press P "
            "first.",
            "Privacy: no tracking, and nothing is sent anywhere.",
            CHROME_MEMORY,
            chrome_remove("ytModify", "ytModify"),
        ],
    },
    "how-many-time": {
        "facts": [
            "What it does: a private one-tap counter for a habit you're cutting down on (smoking, drinking, junk "
            "food, scrolling). Tap the big GUILTY button each time it happens; Undo works for 10 seconds. A heart "
            "per month drains towards a monthly limit you choose, and a chart compares the last seven days with "
            "the week before.",
            "Works on: any phone or computer, in the browser. Nothing to download, no account. Free.",
            "First use: type your name, the habit and a monthly limit, then choose a 4-digit PIN.",
            "Add to Home Screen: on Android, open it in Chrome or Edge, tap the menu, then Install app. On iPhone "
            "or iPad, open it in Safari, tap Share, then Add to Home Screen. On a computer, use the install icon in "
            "Chrome's or Edge's address bar. It then opens full screen, even without internet.",
            "Privacy: everything stays on the device. It asks for the PIN each time; after 7 wrong PINs it warns, "
            "and on the 10th everything is erased. A panic button erases everything after confirming.",
            "Important: there's no online backup. Clearing the browser's data, or changing phone or browser, "
            "starts fresh.",
            "Resource use: it's a small web app that runs in the browser; there are no measured figures, so don't "
            "guess any.",
        ],
    },
}
