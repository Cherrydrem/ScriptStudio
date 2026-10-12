# ScriptStudio 

**Version 1.3.0 · Windows 10/11, 64-bit**

## Features

- Character cards with a picture, name, and optional description.
- Picture-based speaker selection and a speaker dropdown.
- Scene headings, action blocks, and dialogue with optional delivery notes.
- Per-scene location, time, synopsis, and private continuity notes, with a scene overview report.
- Scene board with scene summaries, cast, and whole-scene drag reordering.
- Scene workflow statuses: Draft, Revising, and Locked.
- Character-filtered read-through with timed playback and line navigation.
- Optional character attribution on action blocks, visible in cards and exports.
- Character appearance reports and draggable cast ordering.
- Named draft snapshots and a text/scene-details comparison against the current script.
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

Reorder blocks using the up/down buttons or by dragging in the middle list. Drag-reordering is disabled while a script search is active, so hidden blocks are not accidentally moved. Drag cast cards to change their order. Use **Reports → Scene overview** or **Character appearances** to review the script. Character pictures are writing helpers; they are not included in text or PDF exports.

Use **View → Scene board** to review scenes as cards with their status, synopsis, location, and cast. Drag cards or use the move buttons, then choose **Apply order**; each scene keeps all its action, dialogue, and notes together. Blocks before the first scene remain at the top. Set a scene to Draft, Revising, or Locked in **Scene details**.

Use **View → Read-through** to step through or play dialogue, optionally filtered to one character. Select an action block and use **Action by** to identify who performs it; the character label appears on the block and in exports without changing the action text.

Select a scene and click **Scene details** to record its location, time, synopsis, and private continuity notes. The large editor holds optional scene notes, separate from the scene title; scene notes and continuity notes stay in the editable project and are not included in text or PDF exports. **Drafts → Save named draft** stores a compact comparison snapshot in the project; **Compare draft with current** shows a unified text and scene-details diff. Draft snapshots omit character images to avoid duplicating large embedded files.

## Saving and crash recovery

- **Ctrl+S:** Save. The first save asks for a location.
- **Ctrl+Shift+S:** Save As, with a different filename or location.
- A `✦` at the start of the window title means unsaved changes.
- Saving runs in the background. Wait for **Script saved** before moving or sharing the file.
- If you edit during saving, the newer edits stay unsaved; press **Ctrl+S** again.
- New, Open, and Close offer **Save / Discard / Cancel** when needed.
- Recovery runs every 30 seconds while there are unsaved edits. After an interrupted session, the app offers recovery; you can also use **File → Recover autosaved work**.
- Named draft snapshots are stored inside the project file, so save the project after creating one.

Recovery is a safety net, not a replacement for manual saving. Save recovered work normally and keep separate backups of important projects. Window layout preferences and recovery copies are stored in your Windows user profile. **View → Reset workspace** restores the standard window layout.

## Export your script

| Export | Result |
|---|---|
| **Plain text (.txt)** | UTF-8 text containing scene headings, action, names, delivery notes, and dialogue. |
| **Readable PDF** | A white-page script without cast pictures or the dark interface theme. Export options include screenplay-style US Letter pages, page numbers, and optional scene numbers. |
| **StoryboardStudio project (.sboard)** | Blank 16:9 panels with script text in their notes and scene headings as panel scene labels. |

PDF export supports screenplay-style margins and monospaced type, but pagination is not guaranteed to match every industry screenplay standard or one-page-per-minute timing.

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
