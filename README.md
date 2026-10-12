SCRIPTSTUDIO 
Windows 10 / 11, 64-bit • Version 1.3.0

START HERE
1. Extract this ZIP. Do not run the EXE from ZIP preview.
2. Double-click ScriptStudio.exe. This is a standalone Windows program:
3. First launch can take a moment while the bundled runtime unpacks.
4. For a desktop shortcut, right-click the EXE > Show more options >
   Send to > Desktop (create shortcut). Keep the EXE in the same location.

This is an unsigned build. Windows may show a SmartScreen warning.
Only if you trust the original download, choose More info > Run anyway.
Do not disable antivirus protection. A damaged-file message is not the
same as SmartScreen: download again or report the exact message instead.

A FACE FOR EVERY VOICE
- Choose + Character, upload a picture, give them a name and optionally
  add a description that helps you remember who they are.
- Click a cast picture, then + Dialogue. That character becomes the speaker.
- For existing dialogue, click another picture or use the speaker dropdown.
- Write in the right-hand editor. Choose + Action or + Scene for other text.
- Optional delivery notes: whispering, excited, off-screen, and so on.
- Double-click a character card (or Edit) to rename or replace their picture.
  Renaming updates all linked dialogue. Removing a used character offers
  reassignment or leaves the dialogue unassigned; it never deletes their text.
- Character pictures are embedded as PNGs inside the .scriptstudio file;
  no image sidecars are required. Large pictures are reduced to fit within
  1200 x 1200 pixels while preserving aspect ratio. PNG/JPG/BMP/WebP are good
  choices. Pictures are writing helpers and are not printed in the script.

WRITE AND ORGANISE
Add scene, action and dialogue blocks. Change a block's type at the top
of its editor. Reorder with up/down arrows or drag blocks in the middle list.
Search cast names/descriptions or script text/speaker names. Drag-reorder is
turned off while a script search is active, to avoid moving hidden blocks.
Rename a scene: select it and press F2, or double-click it in the middle list.
Tags: pick a preset (emotions and story notes) or type your own, then click
+ Tag. Click a tag to remove it. Tags show in the script list and are searchable;
they are not printed in exports. Dialogue delivery notes also have an emotion
dropdown, and you can still type anything you like.
Notes: + Note adds a private block that is never exported. Scenes are numbered.
Find and replace: Ctrl+H. Outline button: show only scene headings. Tag filter:
show only blocks with one tag. The status bar shows words, scenes and reading time.
View > Light theme switches colours. Edit > Edit tag presets sets your own tags,
and Export > Include tags in exports adds tags to the output.
Rename a scene with F2, the Rename scene button, or a right-click. Ctrl+B bookmarks a
block (Ctrl+G lists bookmarks, F3 jumps to the next). Colour labels are in the editor
and the right-click menu. Ctrl+Shift+C collapses a scene; View > Collapse all scenes
folds everything. Folding is not saved with the project. Characters can have a role
and age.
File > Import plain text script: INT./EXT./SCENE lines become scenes, NAME: words
or NAME (delivery): words becomes dialogue, other text becomes action. New names
become new characters. File > Title page details adds a PDF title page, and the
Export menu switches the title page and page numbers on or off. File > Auto-backup
folder copies each save to a folder you choose (newest 20 kept per project).
Duplicate or delete a block. Shared Undo/Redo covers text, cast, speakers,
block order and deletion. Typing is grouped into short undo steps.

SAVE AND RECOVER
Ctrl+S saves; Ctrl+Shift+S saves under a new name. Projects use .scriptstudio.
A star-like mark at the start of the window title means unsaved changes.
Saving happens in the background. If you edit during a save, those newer
edits stay unsaved until you save again. New/Open/Close offer Save/Discard/
Cancel when needed. Keep projects in Documents, not beside build files.
Recovery snapshots are written every 30 seconds while work is unsaved.
After an interrupted session, the app offers recovery. You can also use
File > Recover autosaved work. Recovery is not a replacement for Ctrl+S.
Save recovered work normally. Manually backing up your project is advised.
The last ten saved/opened projects appear in File > Recent Projects.
Window size, position and pane widths are remembered for your user account.
View > Reset workspace restores the standard layout.

EXPORT
Export > Plain text: readable UTF-8 text with scene headings, action,
character names, delivery notes and dialogue.
Export > Readable PDF: a white-page script, without cast photos or dark theme.
This is a clear writing format, not a promise of industry-standard screenplay
pagination or one-page-per-minute timing.
Export > StoryboardStudio project: an editable .sboard handoff. Each action
or dialogue becomes a blank 16:9 storyboard panel with the script in notes;
scene headings label the panels. Default duration is 2 seconds per panel.
Open it in StoryboardStudio and draw/set timing there. This is a one-way
export, not live syncing. Cast photos are not imported into the storyboard.

SHORTCUTS
Ctrl+N                  New script
Ctrl+O                  Open project
Ctrl+S                  Save
Ctrl+Shift+S            Save As
Ctrl+Z                  Undo
Ctrl+Y / Ctrl+Shift+Z   Redo
Ctrl+D                  Duplicate selected block
F2                      Rename selected scene
Ctrl+H                  Find and replace
Ctrl+B                  Bookmark block
Ctrl+G                  Go to bookmark
F3                      Next bookmark
Ctrl+Shift+C            Collapse/expand scene
Ctrl+E                  Export PDF
F1                      Quick start / shortcuts

YOUR DATA
Everything is local. There is no cloud upload, tracking, AI writing, or
account. The only internet use is an optional update check: at startup the app
asks GitHub whether a newer release exists, then lets you choose whether to open
the download page. It sends none of your writing. Turn it off any time in
Help > Check for updates when ScriptStudio starts. Preferences and recovery copies live in your Windows user profile.
Delete the EXE to remove the portable app; that does not remove your saved
projects or preferences. To update, close the old app and use the new EXE.

VERIFICATION / LIMITATIONS
The source has automated tests for cast photos, speaker picking, rename,
reassignment, writing, undo/redo, block order, saving/opening, failed saves,
background writes, recovery, exports, recent files and workspace memory.
Windows builds are produced with Windows Python/PyInstaller under Wine.
Real Windows testing is still needed for SmartScreen, antivirus behavior,
font rendering, high-DPI displays and device-specific issues.

Source is supplied separately for learning or rebuilding.
The executable contains Python and Qt (PySide6). Their licenses are included
in THIRD-PARTY-NOTICES.txt and the licenses folder.
