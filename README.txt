# ScriptStudio — Dark Cherry Edition

**Version 1.0.0 · Windows 10/11, 64-bit**

## Features

- Character cards with a picture, name, and optional description.
- Picture-based speaker selection and a speaker dropdown.
- Scene headings, action blocks, and dialogue with optional delivery notes.
- Character renaming updates linked dialogue. Removing a character offers reassignment or leaves their dialogue unassigned without deleting its text.
- Search cast names/descriptions and script text/speakers.
- Reorder blocks with arrows or drag-and-drop; duplicate or delete blocks.
- Shared undo/redo for writing, cast changes, speaker assignments, and block changes.
- Background manual saving and recovery snapshots every 30 seconds while work is unsaved.
- Recent projects and remembered window position, size, and pane widths.
- Plain-text, readable PDF, and StoryboardStudio project exports.

## Download and install

**[Download ScriptStudio-Setup.exe] — approximately **43 MB** (43.20 MiB).

1. Save your work and close any running copy of ScriptStudio.
2. Download and double-click `ScriptStudio-Setup.exe`.
3. Choose an installation folder. The default is `%LOCALAPPDATA%\Programs\ScriptStudio` for your Windows account.
4. Leave **Desktop shortcut** selected if you want one, then click **Install**.
5. Open ScriptStudio from the Desktop or Start Menu shortcut, or use **Open ScriptStudio** on the installer’s final page.

The Windows app includes its runtime. **You do not need to create an account.** No internet connection is required to write after downloading the app.

Prefer a portable copy? (coming soon)

## First launch and Windows warnings

First launch may take a moment while the single-file app unpacks its bundled runtime.

The app and installer are **unsigned**. Windows SmartScreen may warn about an unrecognised app. run anyway! 


## Make your first script

1. Enter your script title above the middle list.
2. Click **+ Character**, choose a picture, enter a name, and optionally add a description.
3. Click their picture, then **+ Dialogue**. That character becomes the speaker.
4. Write in the right-hand editor. Add a delivery note such as “whispering” if useful.
5. Use **+ Action** to describe events and **+ Scene** to separate locations or sections.
6. Press **Ctrl+S** and save your `.scriptstudio` project, preferably in Documents.

To change an existing dialogue’s speaker, select the dialogue and click another character picture or use the speaker dropdown. Double-click a character card, or select it and click **Edit**, to change their name, description, or picture.

The optional `Example.scriptstudio` project is included in the installation folder and portable ZIP. Open it using **File → Open**. Use **Save As** to make your own copy.

### Pictures and organisation

Character pictures are embedded in the project as PNG data, so moving or deleting the original image does not break the script. Images are reduced to fit within 1200 × 1200 pixels while preserving aspect ratio. PNG, JPG, BMP, and WebP are good choices.

Reorder blocks using the up/down buttons or by dragging in the middle list. Drag-reordering is disabled while a script search is active, so hidden blocks are not accidentally moved. Character pictures are writing helpers; they are not included in text or PDF exports.

## Saving and crash recovery

- **Ctrl+S:** Save. The first save asks for a location.
- **Ctrl+Shift+S:** Save As, with a different filename or location.
- A `✦` at the start of the window title means unsaved changes.
- Saving runs in the background. Wait for **Script saved** before moving or sharing the file.
- If you edit during saving, the newer edits stay unsaved; press **Ctrl+S** again.
- New, Open, and Close offer **Save / Discard / Cancel** when needed.
- Recovery runs every 30 seconds while there are unsaved edits. After an interrupted session, the app offers recovery; you can also use **File → Recover autosaved work**.

Recovery is a safety net, not a replacement for manual saving. Save recovered work normally and keep separate backups of important projects. Window layout preferences and recovery copies are stored in your Windows user profile. **View → Reset workspace** restores the standard window layout.

## Export your script

| Export | Result |
|---|---|
| **Plain text (.txt)** | UTF-8 text containing scene headings, action, names, delivery notes, and dialogue. |
| **Readable PDF** | A white-page script without cast pictures or the dark interface theme. |
| **StoryboardStudio project (.sboard)** | Blank 16:9 panels with script text in their notes and scene headings as panel scene labels. |

PDF export is a readable writing format, not a guarantee of industry-standard screenplay pagination or one-page-per-minute timing.

Storyboard export creates one blank panel for each action or dialogue block, with a default duration of 2 seconds. Open the `.sboard` in StoryboardStudio to draw and adjust timing. This is a **one-way handoff, not live syncing**; character pictures are not transferred. Exporting does not replace saving your editable `.scriptstudio` project.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+N | New script |
| Ctrl+O | Open project |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+Z | Undo |
| Ctrl+Y or Ctrl+Shift+Z | Redo |
| Ctrl+D | Duplicate selected block |
| Ctrl+E | Export PDF |
| F1 | Quick start and shortcuts |

## Updating and uninstalling

**Update:** save your project, close ScriptStudio, then run the newer installer. Keep backups before updating.

**Uninstall:** close ScriptStudio, then use **Windows Settings → Apps → ScriptStudio → Uninstall**, or **Start Menu → ScriptStudio → Uninstall**.

The uninstaller removes the app, installed documentation, and shortcuts. It does not delete your script projects, preferences, or recovery directory. It also preserves the supplied example project, so the installation folder may remain afterward.

## Troubleshooting

- **A character cannot be assigned:** select a dialogue block first. Scene and action blocks do not have speakers.
- **An image will not load:** try a valid PNG, JPG, BMP, or WebP file.
- **Drag-reordering does not work:** clear the script search field, or use the arrow buttons.
- **A save fails:** choose **Save As** and a writable folder such as Documents. Your edits remain in the app after a reported save failure.
- **The layout feels cramped:** widen the window, drag the dividers, or choose **View → Reset workspace**.
- **Work was interrupted:** check **File → Recover autosaved work**, then save the recovered project normally.

If a problem persists, keep the exact error text and a screenshot. Never delete your only project copy while troubleshooting.

## Privacy, source, and license

ScriptStudio works with local files. It has no cloud upload, tracking, AI writing, or account system. Your `.scriptstudio` project contains the character names, pictures, and script, so share it only with people you intend to receive that content.

The application source is licensed under the **MIT License**; see `LICENSE.txt`. Bundled Python, Qt/PySide6, fonts, and the packaging bootloader have their own licenses. See `THIRD-PARTY-NOTICES.txt` and the `licenses` folder. Use character images you have permission to share.

## Verification and limitations

All 84 automated checks passed with Windows Python under Wine. The actual standalone EXE was also checked for picture-based speaker selection, editing, undo/redo, timed recovery, saving, and workspace persistence. PDF text and StoryboardStudio interchange were verified separately.

The installer download matches the original build and passes its archive integrity check. These checks do not replace testing the installer wizard, SmartScreen behaviour, fonts, and display scaling on a real Windows PC.
