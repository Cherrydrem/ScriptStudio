"""ScriptStudio: picture-based script writing in a dark cherry workspace."""
import os,sys,json,copy,uuid,base64,tempfile,time,html,re,urllib.request
from pathlib import Path
from PySide6.QtCore import QEvent,Qt,QSize,QTimer,QSettings,QStandardPaths,QBuffer,QByteArray,QIODevice,Signal,QObject,QRunnable,QThreadPool,QUrl
from PySide6.QtGui import QIcon,QImage,QPixmap,QFont,QFontDatabase,QAction,QKeySequence,QUndoStack,QUndoCommand,QTextDocument,QPageSize,QDesktopServices
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QPlainTextEdit,QComboBox,QCheckBox,QListWidget,QListView,QListWidgetItem,QSplitter,QFileDialog,QInputDialog,QMessageBox,QDialog,QDialogButtonBox,QFormLayout,QAbstractItemView,QToolBar
from PySide6.QtPrintSupport import QPrinter
VERSION='1.2.0'
FILTER='ScriptStudio projects (*.scriptstudio)'
# Put your own GitHub name and repository name here to turn on update checking.
UPDATE_API= "https://github.com/Cherrydrem/ScriptStudio'
EMOTIONS=['whispering','shouting','excited','angry','sad','nervous','laughing','crying','sarcastic','calm','off-screen','happy','scared','confused','tired','cheerful','serious','pleading','annoyed','surprised','dreamy','mumbling','singing','under breath','deadpan']
TAG_PRESETS=EMOTIONS[:11]+['flashback','important','needs rewrite','music','sound effect','cut?']
WHATS_NEW="""• Notes: a private block type that is never exported (+ Note)
• Find and replace (Ctrl+H)
• Outline button and a tag filter above the script list
• Word count, scene count and reading time in the status bar
• Scenes are numbered, and cast cards show how many lines each character has
• Light theme (View menu)
• Your own tag presets (Edit menu), and tags can be included in exports (Export menu)
• More emotion presets, and the emotions you type are remembered
"""
FONTS_LOADED=False
def load_fonts():
    global FONTS_LOADED
    if FONTS_LOADED:return
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
    for path in (root/'fonts').glob('*.ttf'):QFontDatabase.addApplicationFont(str(path))
    FONTS_LOADED=True
def uid():return uuid.uuid4().hex
def new_block(kind='scene',speaker=None,text=''):
    return {'id':uid(),'type':kind,'text':text,'speaker':speaker if kind=='dialogue' else None,'delivery':'','tags':[]}
def new_project():return {'format':'ScriptStudio','version':1,'title':'Untitled','characters':[],'blocks':[new_block('scene',text='Scene 1 — ')]}
def image_data(path):
    image=QImage(str(path))
    if image.isNull():raise ValueError('This image cannot be opened. Try PNG, JPG, BMP or WebP.')
    image=image.scaled(1200,1200,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
    buf=QBuffer();buf.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buf,'PNG'):raise ValueError('Could not encode image.')
    return base64.b64encode(bytes(buf.data())).decode('ascii')
def picture(data,size=72):
    pix=QPixmap()
    if data:pix.loadFromData(base64.b64decode(data))
    if pix.isNull():
        pix=QPixmap(size,size);pix.fill(Qt.GlobalColor.transparent)
    return pix.scaled(size,size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
def atomic_json(path,value):
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+target.name+'-',suffix='.tmp',dir=str(target.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(value,f,ensure_ascii=False,separators=(',',':'));f.flush();os.fsync(f.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def validate(data):
    if not isinstance(data,dict) or data.get('format')!='ScriptStudio' or data.get('version')!=1:raise ValueError('Not a supported ScriptStudio project.')
    if not isinstance(data.get('title'),str):raise ValueError('Invalid title.')
    chars=data.get('characters');blocks=data.get('blocks')
    if not isinstance(chars,list) or not isinstance(blocks,list):raise ValueError('Missing cast or script blocks.')
    ids=set()
    for c in chars:
        if not isinstance(c,dict) or not isinstance(c.get('id'),str) or c['id'] in ids or not isinstance(c.get('name'),str) or not c['name'].strip():raise ValueError('Invalid character.')
        ids.add(c['id'])
        for field in ('image','description'):
            if not isinstance(c.get(field,''),str):raise ValueError('Invalid character image or description.')
        if c.get('image'):
            binary=base64.b64decode(c['image'],validate=True);im=QImage.fromData(binary)
            if im.isNull():raise ValueError('Damaged character image.')
    bids=set()
    for b in blocks:
        if not isinstance(b,dict) or not isinstance(b.get('id'),str) or b['id'] in bids or b.get('type') not in ('scene','action','dialogue','note'):raise ValueError('Invalid script block.')
        bids.add(b['id'])
        if not isinstance(b.get('text'),str) or not isinstance(b.get('delivery',''),str):raise ValueError('Invalid script text.')
        if b.get('speaker') is not None and b.get('speaker') not in ids:raise ValueError('Unknown speaker reference.')
        # Tags are optional, so older projects without them still open.
        if not isinstance(b.get('tags',[]),list) or not all(isinstance(t,str) for t in b.get('tags',[])):raise ValueError('Invalid tags.')
    return data
class JobSignals(QObject):done=Signal(object,str)
class WriteJob(QRunnable):
    def __init__(self,path,data,context):super().__init__();self.path=path;self.data=data;self.context=context;self.signals=JobSignals()
    def run(self):
        error=''
        try:atomic_json(self.path,self.data)
        except Exception as e:error=str(e)
        self.signals.done.emit(self.context,error)
def version_tuple(text):
    # 'v1.10.2' becomes (1, 10, 2), so versions compare as numbers, not as text.
    numbers=[int(n) for n in re.findall(r'\d+',str(text))[:3]]
    return tuple(numbers+[0]*(3-len(numbers)))
class UpdateJob(QRunnable):
    # Asks GitHub for the latest release in the background, so the app never freezes.
    def __init__(self,url,context):super().__init__();self.url=url;self.context=context;self.signals=JobSignals()
    def run(self):
        error='';info={}
        try:
            request=urllib.request.Request(self.url,headers={'User-Agent':'ScriptStudio','Accept':'application/vnd.github+json'})
            with urllib.request.urlopen(request,timeout=6) as response:info=json.loads(response.read(200000).decode('utf-8'))
        except Exception as e:error=str(e) or 'Could not reach GitHub.'
        self.signals.done.emit({'context':self.context,'info':info},error)
class Edit(QUndoCommand):
    def __init__(self,win,before,after,before_id,after_id,label,key):
        super().__init__(label);self.win=win;self.before=before;self.after=after;self.before_id=before_id;self.after_id=after_id;self.key=key;self.when=time.monotonic();self.first=True
    def redo(self):
        if self.first:self.first=False
        else:self.win.restore(self.after,self.after_id)
    def undo(self):self.win.restore(self.before,self.before_id)
    def id(self):return 201 if self.key else -1
    def mergeWith(self,other):
        if not isinstance(other,Edit) or self.key!=other.key or other.when-self.when>.8:return False
        self.after=other.after;self.after_id=other.after_id;self.when=other.when;return True
class CharacterDialog(QDialog):
    def __init__(self,parent,character=None):
        super().__init__(parent);self.setWindowTitle('Edit character' if character else 'Add character');self.resize(410,390)
        self.character=copy.deepcopy(character) if character else {'id':uid(),'name':'','description':'','image':''}
        layout=QVBoxLayout(self);self.photo=QLabel();self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter);self.photo.setMinimumHeight(110);layout.addWidget(self.photo)
        image_button=QPushButton('Choose picture…');image_button.clicked.connect(self.choose);layout.addWidget(image_button)
        form=QFormLayout();self.name=QLineEdit(self.character['name']);self.name.setPlaceholderText('Name you want above their dialogue')
        self.description=QPlainTextEdit(self.character.get('description',''));self.description.setPlaceholderText('Optional reminder: appearance, personality, role…');self.description.setMaximumHeight(95)
        form.addRow('Name',self.name);form.addRow('Description',self.description);layout.addLayout(form)
        self.error=QLabel();self.error.setWordWrap(True);layout.addWidget(self.error)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons);self.preview()
    def preview(self):
        if self.character.get('image'):self.photo.setPixmap(picture(self.character['image'],100))
        else:self.photo.setText('A picture helps you recognise the speaker')
    def choose(self):
        path,_=QFileDialog.getOpenFileName(self,'Character picture','','Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)')
        if not path:return
        try:self.character['image']=image_data(path);self.preview();self.error.clear()
        except Exception as e:self.error.setText(str(e))
    def accept(self):
        if not self.name.text().strip():self.error.setText('Please give this character a name.');return
        self.character['name']=self.name.text().strip();self.character['description']=self.description.toPlainText();super().accept()
STYLE='''
QWidget { background: #190f15; color: #f8eaf0; font-family: "DejaVu Sans", sans-serif; font-size: 13px; }
QMainWindow, QDialog { background: #190f15; }
QMenuBar, QToolBar { background: #29151f; border: none; padding: 5px; }
QMenuBar::item:selected, QMenu::item:selected { background: #822b49; }
QMenu { background: #29151f; border: 1px solid #764151; padding: 5px; }
QPushButton, QToolButton { background: #492132; border: 1px solid #75404e; border-radius: 6px; padding: 7px 10px; }
QPushButton:hover, QToolButton:hover { background: #71304a; border-color: #da6c8b; }
QPushButton:pressed { background: #992c51; }
QPushButton:disabled, QToolButton:disabled { color: #997981; background: #2b1921; border-color: #442a32; }
QLineEdit, QPlainTextEdit, QComboBox { background: #24151c; border: 1px solid #724051; border-radius: 6px; padding: 7px; selection-background-color: #943756; selection-color: #fff6fa; }
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #e17b99; }
QComboBox QAbstractItemView { background: #2d1923; selection-background-color: #822b49; }
QListWidget { background: #21131a; border: 1px solid #58303e; border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { border-radius: 6px; padding: 9px; margin: 2px; }
QListWidget::item:selected { background: #6b263f; color: #fff3f8; border: 1px solid #d26b8a; }
QListWidget::item:hover:!selected { background: #402031; }
QLabel#heading { color: #f09bb3; font-size: 19px; font-weight: 600; }
QLabel#muted { color: #c8a5b3; }
QSplitter::handle { background: #543040; }
QSplitter::handle:hover { background: #bb4d72; }
QStatusBar { background: #29151f; color: #d4b0be; }
QScrollBar:vertical { background: #25141d; width: 12px; }
QScrollBar::handle:vertical { background: #85405a; min-height: 24px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #482434; color: #fff3f7; border: 1px solid #c56184; }
'''
# The light theme is the dark theme with every colour swapped for a light partner.
LIGHT_COLORS={'#190f15':'#fbf3f6','#f8eaf0':'#2b1520','#29151f':'#f1dde6','#822b49':'#e9a9bf','#764151':'#c99aab','#492132':'#f0d4de','#75404e':'#c58b9d','#71304a':'#e7b3c6','#da6c8b':'#b8466a','#992c51':'#dc8aa6','#997981':'#a98d97','#2b1921':'#f5e6ec','#442a32':'#dcc0ca','#24151c':'#ffffff','#724051':'#cfa1b2','#943756':'#f0a3bd','#fff6fa':'#2b1520','#e17b99':'#c4577a','#2d1923':'#ffffff','#21131a':'#fff9fb','#58303e':'#d7b3c1','#6b263f':'#f2b8cc','#fff3f8':'#2b1520','#d26b8a':'#c4577a','#402031':'#f6dde7','#f09bb3':'#a8325b','#c8a5b3':'#7a5666','#543040':'#dcc0ca','#bb4d72':'#c4577a','#d4b0be':'#5c3a48','#25141d':'#f1dde6','#85405a':'#c58b9d','#482434':'#ffffff','#fff3f7':'#2b1520','#c56184':'#c4577a'}
LIGHT_STYLE=re.sub(r'#[0-9a-fA-F]{6}',lambda m:LIGHT_COLORS.get(m.group(0).lower(),m.group(0)),STYLE)
class FindReplaceDialog(QDialog):
    def __init__(self,parent):
        super().__init__(parent);self.setWindowTitle('Find and replace');form=QFormLayout(self)
        self.find=QLineEdit();self.replace=QLineEdit();self.case=QCheckBox('Match upper/lower case')
        form.addRow('Find',self.find);form.addRow('Replace with',self.replace);form.addRow('',self.case)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Replace all');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)
class Window(QMainWindow):
    def __init__(self,recovery_prompt=True):
        super().__init__();load_fonts();self.resize(1220,810);self.setMinimumSize(850,580);self.setAcceptDrops(True)
        settings=os.environ.get('SS_SETTINGS_FILE')
        self.settings=QSettings(settings,QSettings.Format.IniFormat) if settings else QSettings('ScriptStudio','ScriptStudio')
        self.project=new_project();self.path='';self.selected=self.project['blocks'][0]['id'];self.default_speaker=None;self.restoring=False;self.recovered_dirty=False;self.saving=False;self.save_success=False;self.revision=0;self.jobs=[];self.recovery_busy=False
        directory=os.environ.get('SS_RECOVERY_DIR') or os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation),'recovery')
        self.recovery_file=Path(directory)/('session-'+uid()+'.json');self.pool=QThreadPool(self);self.pool.setMaxThreadCount(1)
        self.history=QUndoStack(self);self.history.setUndoLimit(100)
        self.build_ui();self.build_menus();self.history.indexChanged.connect(self.history_state);self.history.cleanChanged.connect(self.history_state)
        for editor in (self.text,self.title_edit,self.delivery.lineEdit(),self.tag_combo.lineEdit()):editor.installEventFilter(self)
        self.refresh();self.history.setClean();self.restore_workspace();self.apply_theme()
        self.timer=QTimer(self);self.timer.setInterval(30000);self.timer.timeout.connect(self.autosave);self.timer.start()
        if recovery_prompt:QTimer.singleShot(100,self.offer_recovery)
        if recovery_prompt and self.settings.value('check_updates',True,type=bool):QTimer.singleShot(1500,self.check_updates)
        if recovery_prompt:QTimer.singleShot(900,self.maybe_whats_new)
    def button(self,text,fn,layout):
        b=QPushButton(text);b.clicked.connect(fn);layout.addWidget(b);return b
    def heading(self,text,layout):
        l=QLabel(text);l.setObjectName('heading');layout.addWidget(l);return l
    def build_ui(self):
        central=QWidget();self.setCentralWidget(central);layout=QVBoxLayout(central);layout.setContentsMargins(14,12,14,10)
        top=QHBoxLayout();self.heading('ScriptStudio',top);tag=QLabel('A face for every voice.');tag.setObjectName('muted');top.addWidget(tag);top.addStretch();layout.addLayout(top)
        self.splitter=QSplitter(Qt.Orientation.Horizontal);self.splitter.setHandleWidth(8);layout.addWidget(self.splitter,1)
        cast=QWidget();cl=QVBoxLayout(cast);cl.setContentsMargins(0,0,7,0);self.heading('CAST',cl)
        self.cast_search=QLineEdit();self.cast_search.setPlaceholderText('Find a character…');self.cast_search.textChanged.connect(self.filter_cast);cl.addWidget(self.cast_search)
        hint=QLabel('Click a picture to choose the speaker.');hint.setObjectName('muted');hint.setWordWrap(True);cl.addWidget(hint)
        self.cast=QListWidget();self.cast.setIconSize(QSize(72,72));self.cast.setWordWrap(True);self.cast.itemClicked.connect(self.cast_clicked);self.cast.itemDoubleClicked.connect(lambda _:self.edit_character());cl.addWidget(self.cast,1)
        self.character_description=QLabel();self.character_description.setWordWrap(True);self.character_description.setObjectName('muted');cl.addWidget(self.character_description)
        self.button('+ Character',self.add_character,cl);r=QHBoxLayout();self.edit_character_button=self.button('Edit',self.edit_character,r);self.remove_character_button=self.button('Remove',self.remove_character,r);cl.addLayout(r)
        self.splitter.addWidget(cast)
        middle=QWidget();ml=QVBoxLayout(middle);ml.setContentsMargins(5,0,5,0);self.heading('SCRIPT',ml)
        self.title_edit=QLineEdit();self.title_edit.setPlaceholderText('Script title');self.title_edit.textChanged.connect(self.title_changed);ml.addWidget(self.title_edit)
        self.block_search=QLineEdit();self.block_search.setPlaceholderText('Find text, scenes, or a speaker…');self.block_search.textChanged.connect(self.filter_blocks);ml.addWidget(self.block_search)
        row=QHBoxLayout();self.tag_filter=QComboBox();self.tag_filter.addItem('All tags',None);self.tag_filter.currentIndexChanged.connect(self.filter_blocks);row.addWidget(self.tag_filter,1)
        self.outline_button=self.button('Outline',self.filter_blocks,row);self.outline_button.setCheckable(True);self.outline_button.setToolTip('Show only scene headings');ml.addLayout(row)
        self.blocks=QListWidget();self.blocks.setWordWrap(True);self.blocks.setSpacing(3);self.blocks.currentItemChanged.connect(self.block_selected);self.blocks.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove);self.blocks.setDefaultDropAction(Qt.DropAction.MoveAction);self.blocks.model().rowsMoved.connect(self.rows_moved);self.blocks.itemDoubleClicked.connect(self.rename_scene);ml.addWidget(self.blocks,1)
        row=QHBoxLayout();self.button('+ Dialogue',lambda:self.add_block('dialogue'),row);self.button('+ Action',lambda:self.add_block('action'),row);self.button('+ Scene',lambda:self.add_block('scene'),row);self.button('+ Note',lambda:self.add_block('note'),row);ml.addLayout(row)
        row=QHBoxLayout();self.up_button=self.button('↑',lambda:self.move_block(-1),row);self.down_button=self.button('↓',lambda:self.move_block(1),row);self.duplicate_button=self.button('Duplicate',self.duplicate_block,row);self.delete_button=self.button('Delete',self.delete_block,row);ml.addLayout(row)
        self.splitter.addWidget(middle)
        editor=QWidget();el=QVBoxLayout(editor);el.setContentsMargins(7,0,0,0);self.editor_heading=self.heading('SCENE',el)
        self.type_combo=QComboBox();self.type_combo.addItem('Scene heading','scene');self.type_combo.addItem('Action','action');self.type_combo.addItem('Dialogue','dialogue');self.type_combo.addItem('Note (never exported)','note');self.type_combo.currentIndexChanged.connect(self.type_changed);el.addWidget(self.type_combo)
        self.speaker_label=QLabel('Speaker');el.addWidget(self.speaker_label);self.speaker_combo=QComboBox();self.speaker_combo.setIconSize(QSize(34,34));self.speaker_combo.currentIndexChanged.connect(self.speaker_changed);el.addWidget(self.speaker_combo)
        self.delivery_label=QLabel('Delivery note (optional)');el.addWidget(self.delivery_label);self.delivery=QComboBox();self.delivery.setEditable(True);self.delivery.setInsertPolicy(QComboBox.InsertPolicy.NoInsert);self.delivery.addItems(EMOTIONS);self.delivery.setCurrentIndex(-1);self.delivery.lineEdit().setPlaceholderText('pick an emotion or type your own…');self.delivery.currentTextChanged.connect(self.delivery_changed);el.addWidget(self.delivery)
        # Tags: pick a preset or type your own. Click a tag below to remove it.
        self.tag_label=QLabel('Tags');el.addWidget(self.tag_label);row=QHBoxLayout()
        self.tag_combo=QComboBox();self.tag_combo.setEditable(True);self.tag_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert);self.tag_combo.lineEdit().setPlaceholderText('pick a tag or type your own…')
        self.tag_combo.textActivated.connect(self.add_tag);self.tag_combo.lineEdit().returnPressed.connect(lambda:self.add_tag(self.tag_combo.currentText()));row.addWidget(self.tag_combo,1)
        self.tag_add=self.button('+ Tag',lambda:self.add_tag(self.tag_combo.currentText()),row);el.addLayout(row)
        self.tag_list=QListWidget();self.tag_list.setFlow(QListView.Flow.LeftToRight);self.tag_list.setWrapping(True);self.tag_list.setResizeMode(QListView.ResizeMode.Adjust);self.tag_list.setSpacing(4);self.tag_list.setMaximumHeight(104)
        self.tag_list.setToolTip('Click a tag to remove it.');self.tag_list.itemClicked.connect(self.remove_tag);el.addWidget(self.tag_list)
        self.text=QPlainTextEdit();self.text.setPlaceholderText('Write here…');self.text.setUndoRedoEnabled(False);self.text.setFont(QFont('DejaVu Sans',13));self.text.textChanged.connect(self.text_changed);el.addWidget(self.text,1)
        self.editor_hint=QLabel('Scene headings separate the story. Action describes what happens. Dialogue uses your cast.');self.editor_hint.setWordWrap(True);self.editor_hint.setObjectName('muted');el.addWidget(self.editor_hint)
        self.splitter.addWidget(editor);self.splitter.setSizes([235,450,450]);self.splitter.setChildrenCollapsible(False)
        self.statusBar().showMessage('Add a character picture, then choose + Dialogue.');self.count_label=QLabel('');self.statusBar().addPermanentWidget(self.count_label);self.recovery_label=QLabel('Recovery every 30s');self.statusBar().addPermanentWidget(self.recovery_label)
    def action(self,menu,label,shortcut,fn):
        a=QAction(label,self)
        if shortcut:a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(fn);menu.addAction(a);return a
    def build_menus(self):
        f=self.menuBar().addMenu('File');self.new_action=self.action(f,'New','Ctrl+N',self.new);self.open_action=self.action(f,'Open…','Ctrl+O',self.open_dialog);self.save_action=self.action(f,'Save','Ctrl+S',self.save);self.saveas_action=self.action(f,'Save As…','Ctrl+Shift+S',self.save_as);self.recent=f.addMenu('Recent Projects');self.update_recent();f.addSeparator();self.action(f,'Recover autosaved work…',None,self.recover_dialog);self.action(f,'Exit','Alt+F4',self.close)
        e=self.menuBar().addMenu('Edit');self.undo_action=self.action(e,'Undo','Ctrl+Z',self.undo);self.redo_action=self.action(e,'Redo','Ctrl+Y',self.redo);self.redo_extra=QAction(self);self.redo_extra.setShortcut('Ctrl+Shift+Z');self.redo_extra.triggered.connect(self.redo);self.addAction(self.redo_extra)
        self.action(e,'Duplicate block','Ctrl+D',self.duplicate_block)
        self.action(e,'Rename scene…','F2',self.rename_scene)
        self.action(e,'Find and replace…','Ctrl+H',self.find_replace);self.action(e,'Edit tag presets…',None,self.edit_tag_presets)
        export=self.menuBar().addMenu('Export');self.action(export,'Plain text (.txt)…',None,lambda:self.export_dialog('txt'));self.action(export,'Readable PDF…','Ctrl+E',lambda:self.export_dialog('pdf'));self.action(export,'StoryboardStudio project (.sboard)…',None,lambda:self.export_dialog('sboard'))
        self.tags_export_action=self.action(export,'Include tags in exports',None,lambda on:self.settings.setValue('export_tags',on));self.tags_export_action.setCheckable(True);self.tags_export_action.setChecked(self.settings.value('export_tags',False,type=bool))
        view=self.menuBar().addMenu('View');self.action(view,'Reset workspace',None,self.reset_workspace);self.theme_action=self.action(view,'Light theme',None,self.toggle_theme);self.theme_action.setCheckable(True);self.theme_action.setChecked(self.settings.value('light_theme',False,type=bool))
        h=self.menuBar().addMenu('Help');self.action(h,'Quick start / shortcuts','F1',self.help);self.action(h,'About',None,lambda:QMessageBox.information(self,'About ScriptStudio',f'ScriptStudio {VERSION}\nPicture-based script writing.\nDark cherry edition.\nLocal files; no account or internet required.'))
        h.addSeparator();self.action(h,'Check for updates now…',None,lambda:self.check_updates(True))
        self.update_action=self.action(h,'Check for updates when ScriptStudio starts',None,lambda on:self.settings.setValue('check_updates',on));self.update_action.setCheckable(True);self.update_action.setChecked(self.settings.value('check_updates',True,type=bool))
        tb=QToolBar('Main');tb.setObjectName('MainToolbar');tb.setMovable(False);self.addToolBar(tb)
        for a in (self.new_action,self.open_action,self.save_action,self.undo_action,self.redo_action):tb.addAction(a)
    def current_block(self):return next((b for b in self.project['blocks'] if b['id']==self.selected),None)
    def character(self,ident):return next((c for c in self.project['characters'] if c['id']==ident),None)
    def speaker_name(self,ident):
        c=self.character(ident);return c['name'] if c else '[Choose speaker]'
    def mutate(self,label,fn,key=None,refresh=True):
        if self.restoring:return
        before=copy.deepcopy(self.project);before_id=self.selected;fn()
        if self.project==before:return
        self.revision+=1;after=copy.deepcopy(self.project)
        if self.history.isClean():key=None
        self.history.push(Edit(self,before,after,before_id,self.selected,label,key))
        if refresh:self.refresh()
        else:self.update_block_preview();self.update_title();self.filter_blocks()
    def restore(self,data,selected):
        self.project=copy.deepcopy(data);self.selected=selected;self.revision+=1
        if not self.character(self.default_speaker):self.default_speaker=None
        self.refresh()
    def dirty(self):return self.recovered_dirty or not self.history.isClean()
    def history_state(self,*_):
        self.undo_action.setEnabled(self.history.canUndo());self.redo_action.setEnabled(self.history.canRedo())
        self.undo_action.setText('Undo '+self.history.undoText() if self.history.canUndo() else 'Undo');self.redo_action.setText('Redo '+self.history.redoText() if self.history.canRedo() else 'Redo');self.undo_action.setIconText('Undo');self.redo_action.setIconText('Redo');self.update_title()
    def update_title(self):self.setWindowTitle(('✦ ' if self.dirty() else '')+self.project['title']+' — ScriptStudio')
    def eventFilter(self,obj,event):
        if obj in (self.text,self.title_edit,self.delivery.lineEdit(),self.tag_combo.lineEdit()) and event.type() in (QEvent.Type.ShortcutOverride,QEvent.Type.KeyPress):
            undo=event.matches(QKeySequence.StandardKey.Undo);redo=event.matches(QKeySequence.StandardKey.Redo)
            if undo or redo:
                event.accept()
                if event.type()==QEvent.Type.KeyPress:
                    if undo:self.undo()
                    else:self.redo()
                return True
        return super().eventFilter(obj,event)
    def undo(self):self.history.undo()
    def redo(self):self.history.redo()
    def block_preview(self,b):
        kind=b['type'];header='NOTE' if kind=='note' else 'ACTION' if kind=='action' else self.speaker_name(b.get('speaker')).upper() if kind=='dialogue' else 'SCENE '+str(self.scene_number(b))
        if b['type']=='dialogue' and b.get('delivery'):header+='  ('+b['delivery']+')'
        if b.get('tags'):header+='   ['+', '.join(b['tags'])+']'
        text=b['text'].replace('\n',' ')
        return header+'\n'+(text[:145]+'…' if len(text)>145 else text or 'Click to write…')
    def refresh(self):
        self.restoring=True
        try:
            self.title_edit.setText(self.project['title']);self.cast.clear();self.speaker_combo.clear();self.speaker_combo.addItem('Choose a character…',None)
            for c in self.project['characters']:
                icon=QIcon(picture(c.get('image','')));lines=sum(1 for x in self.project['blocks'] if x.get('speaker')==c['id']);item=QListWidgetItem(icon,c['name']+'\n'+str(lines)+(' line' if lines==1 else ' lines'));item.setData(Qt.ItemDataRole.UserRole,c['id']);item.setToolTip(c.get('description','') or c['name']);item.setSizeHint(QSize(170,92));self.cast.addItem(item);self.speaker_combo.addItem(icon,c['name'],c['id'])
                if c['id']==self.default_speaker:self.cast.setCurrentItem(item)
            self.blocks.clear()
            for b in self.project['blocks']:
                item=QListWidgetItem(self.block_preview(b));item.setData(Qt.ItemDataRole.UserRole,b['id']);item.setSizeHint(QSize(250,88));c=self.character(b.get('speaker'))
                if c and c.get('image'):item.setIcon(QIcon(picture(c['image'],40)))
                self.blocks.addItem(item)
                if b['id']==self.selected:self.blocks.setCurrentItem(item)
            if not self.current_block():
                self.selected=self.project['blocks'][0]['id'] if self.project['blocks'] else None
                if self.blocks.count():self.blocks.setCurrentRow(0)
            self.fill_tag_filter();self.load_editor();self.filter_cast();self.filter_blocks();self.character_state();self.update_counts()
        finally:self.restoring=False
        self.update_title()
    def load_editor(self):
        old=self.restoring;self.restoring=True
        try:
            b=self.current_block();enabled=b is not None
            for widget in (self.type_combo,self.text,self.delivery,self.speaker_combo,self.duplicate_button,self.delete_button,self.tag_combo,self.tag_add,self.tag_list):widget.setEnabled(enabled)
            self.up_button.setEnabled(enabled and self.block_index()>0);self.down_button.setEnabled(enabled and self.block_index()<len(self.project['blocks'])-1)
            kind=b['type'] if b else 'scene';dialogue=kind=='dialogue' and enabled
            self.type_combo.setCurrentIndex(self.type_combo.findData(kind));self.editor_heading.setText(kind.upper() if enabled else 'ADD A BLOCK');self.text.setPlainText(b['text'] if b else '')
            for widget in (self.speaker_label,self.speaker_combo,self.delivery_label,self.delivery):widget.setVisible(dialogue)
            self.speaker_combo.setCurrentIndex(max(0,self.speaker_combo.findData(b.get('speaker') if b else None)));self.fill_emotions();self.delivery.setCurrentText(b.get('delivery','') if b else '');self.load_tags(b)
            self.text.setPlaceholderText({'scene':'Scene 1 — Bedroom, night','action':'Describe what happens…','dialogue':'What do they say?','note':'A private note to yourself. It is never exported…'}[kind])
        finally:self.restoring=old
    def update_block_preview(self):
        self.update_counts();b=self.current_block()
        if not b:return
        for i in range(self.blocks.count()):
            item=self.blocks.item(i)
            if item.data(Qt.ItemDataRole.UserRole)==b['id']:item.setText(self.block_preview(b));break
    def block_selected(self,current,previous):
        if self.restoring:return
        self.selected=current.data(Qt.ItemDataRole.UserRole) if current else None;self.load_editor()
    def block_index(self):return next((i for i,b in enumerate(self.project['blocks']) if b['id']==self.selected),-1)
    def add_block(self,kind):
        def change():
            b=new_block(kind,self.default_speaker);index=self.block_index();self.project['blocks'].insert(index+1 if index>=0 else len(self.project['blocks']),b);self.selected=b['id']
        self.block_search.clear();self.mutate('Add '+kind,change);self.text.setFocus()
    def duplicate_block(self):
        b=self.current_block()
        if not b:return
        def change():
            item=copy.deepcopy(b);item['id']=uid();self.project['blocks'].insert(self.block_index()+1,item);self.selected=item['id']
        self.mutate('Duplicate block',change)
    def delete_block(self):
        index=self.block_index()
        if index<0:return
        if self.current_block()['text'].strip() and QMessageBox.question(self,'Delete block','Delete this script block? You can undo this.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        def change():
            self.project['blocks'].pop(index);self.selected=self.project['blocks'][min(index,len(self.project['blocks'])-1)]['id'] if self.project['blocks'] else None
        self.mutate('Delete block',change)
    def move_block(self,delta):
        i=self.block_index();j=i+delta
        if i<0 or not 0<=j<len(self.project['blocks']):return
        def change():self.project['blocks'].insert(j,self.project['blocks'].pop(i))
        self.mutate('Reorder block',change)
    def rows_moved(self,*_):
        if self.restoring:return
        ids=[self.blocks.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.blocks.count())];mapping={b['id']:b for b in self.project['blocks']}
        if set(ids)==set(mapping):self.mutate('Reorder blocks',lambda:self.project.update(blocks=[mapping[i] for i in ids]))
    def tag_presets(self):
        saved=self.settings.value('tag_presets',[],type=list)
        if isinstance(saved,str):saved=[saved]
        return [str(t) for t in saved if str(t).strip()] or list(TAG_PRESETS)
    def edit_tag_presets(self):
        text,ok=QInputDialog.getMultiLineText(self,'Tag presets','One tag per line. Leave it empty to restore the standard list.','\n'.join(self.tag_presets()))
        if not ok:return
        tags=[];seen=set()
        for line in text.splitlines():
            tag=' '.join(line.split())[:40]
            if tag and tag.casefold() not in seen:seen.add(tag.casefold());tags.append(tag)
        if tags:self.settings.setValue('tag_presets',tags)
        else:self.settings.remove('tag_presets')
        self.load_tags(self.current_block())
    def fill_emotions(self):
        # The emotion dropdown offers the presets plus every emotion you have typed before.
        used=sorted({x.get('delivery','') for x in self.project['blocks'] if x.get('delivery')}-set(EMOTIONS),key=str.casefold)
        self.delivery.blockSignals(True);self.delivery.clear();self.delivery.addItems(EMOTIONS+used);self.delivery.blockSignals(False)
    def fill_tag_filter(self):
        current=self.tag_filter.currentData();used=sorted({t for x in self.project['blocks'] for t in x.get('tags',[])},key=str.casefold)
        self.tag_filter.blockSignals(True);self.tag_filter.clear();self.tag_filter.addItem('All tags',None)
        for t in used:self.tag_filter.addItem(t,t)
        self.tag_filter.setCurrentIndex(max(0,self.tag_filter.findData(current)));self.tag_filter.blockSignals(False)
    def scene_number(self,block):
        number=0
        for x in self.project['blocks']:
            if x['type']=='scene':number+=1
            if x['id']==block['id']:break
        return number
    def update_counts(self):
        blocks=self.project['blocks'];words=sum(len(b['text'].split()) for b in blocks if b['type']!='note');scenes=sum(1 for b in blocks if b['type']=='scene')
        minutes=max(1,round(words/200)) if words else 0
        self.count_label.setText(f'{words:,} words · {scenes} scene{"" if scenes==1 else "s"} · ~{minutes} min read   ')
    def replace_all(self,find,replace,match_case=False):
        pattern=re.compile(re.escape(find),0 if match_case else re.IGNORECASE)
        count=sum(len(pattern.findall(b['text'])) for b in self.project['blocks'])
        if count:
            def change():
                for b in self.project['blocks']:b['text']=pattern.sub(lambda m:replace,b['text'])
            self.mutate('Replace all',change)
        return count
    def find_replace(self):
        dialog=FindReplaceDialog(self)
        if dialog.exec()!=QDialog.DialogCode.Accepted or not dialog.find.text():return
        count=self.replace_all(dialog.find.text(),dialog.replace.text(),dialog.case.isChecked())
        QMessageBox.information(self,'Find and replace',f'Replaced {count} place(s).' if count else 'Nothing found.')
    def apply_theme(self):
        QApplication.instance().setStyleSheet(LIGHT_STYLE if self.settings.value('light_theme',False,type=bool) else STYLE)
    def toggle_theme(self,on):
        self.settings.setValue('light_theme',on);self.apply_theme()
    def maybe_whats_new(self):
        seen=self.settings.value('seen_version','');self.settings.setValue('seen_version',VERSION)
        if seen!=VERSION:QMessageBox.information(self,"What's new in "+VERSION,WHATS_NEW)
    def load_tags(self,b):
        # The dropdown offers the presets plus every custom tag already used in this script.
        used=sorted({t for x in self.project['blocks'] for t in x.get('tags',[])},key=str.casefold)
        self.tag_combo.clear();presets=self.tag_presets();self.tag_combo.addItems(presets+[t for t in used if t not in presets]);self.tag_combo.setCurrentIndex(-1)
        self.tag_list.clear()
        for tag in (b.get('tags',[]) if b else []):
            item=QListWidgetItem(tag+'  ✕');item.setData(Qt.ItemDataRole.UserRole,tag);self.tag_list.addItem(item)
    def add_tag(self,text):
        b=self.current_block();tag=' '.join(str(text).split())[:40]
        if not b or self.restoring or not tag:return
        if tag.casefold() in [t.casefold() for t in b.get('tags',[])]:self.tag_combo.clearEditText();return
        self.mutate('Add tag',lambda:b.setdefault('tags',[]).append(tag))
    def remove_tag(self,item):
        b=self.current_block();tag=item.data(Qt.ItemDataRole.UserRole)
        if b and tag in b.get('tags',[]):self.mutate('Remove tag',lambda:b['tags'].remove(tag))
    def rename_scene(self,*_):
        b=self.current_block()
        if not b or b['type']!='scene':self.statusBar().showMessage('Select a scene heading, then press F2 to rename it.');return
        current=' '.join(b['text'].splitlines())
        name,ok=QInputDialog.getText(self,'Rename scene','Scene name:',text=current)
        name=name.strip()
        if ok and name and name!=current:self.mutate('Rename scene',lambda:b.update(text=name))
    def check_updates(self,manual=False):
        if 'YOUR-NAME' in UPDATE_API:
            if manual:QMessageBox.information(self,'Check for updates','Update checking is not set up yet.\nPut your GitHub name and repository in UPDATE_API near the top of scriptstudio.py.')
            return False
        context={'manual':manual};job=UpdateJob(UPDATE_API,context);job.signals.done.connect(self.update_check_done);self.jobs.append(job);QThreadPool.globalInstance().start(job);return True
    def update_check_done(self,result,error):
        context=result['context'];self.jobs=[j for j in self.jobs if j.context is not context];manual=context['manual'];info=result['info']
        if error:
            if manual:QMessageBox.information(self,'Check for updates','Could not check for updates right now.\n'+error)
            return
        tag=str(info.get('tag_name',''));link=str(info.get('html_url',''))
        if version_tuple(tag)>version_tuple(VERSION) and link.startswith('https://github.com/'):
            answer=QMessageBox.question(self,'Update available',f'ScriptStudio {tag.lstrip("vV")} is available. You have {VERSION}.\n\nOpen the download page? Nothing is installed automatically.')
            if answer==QMessageBox.StandardButton.Yes:QDesktopServices.openUrl(QUrl(link))
        elif manual:QMessageBox.information(self,'Check for updates','You have the latest version.')
    def text_changed(self):
        b=self.current_block()
        if b and not self.restoring:
            value=self.text.toPlainText();self.mutate('Write '+b['type'],lambda:b.update(text=value),'text:'+b['id'],False)
    def title_changed(self,value):
        if not self.restoring:self.mutate('Script title',lambda:self.project.update(title=value),'title',False)
    def delivery_changed(self,value):
        b=self.current_block()
        if b and not self.restoring:self.mutate('Delivery note',lambda:b.update(delivery=value),'delivery:'+b['id'],False)
    def type_changed(self):
        b=self.current_block()
        if not b or self.restoring:return
        kind=self.type_combo.currentData()
        def change():b.update(type=kind,speaker=self.default_speaker if kind=='dialogue' else None,delivery='')
        self.mutate('Change block type',change)
    def speaker_changed(self):
        b=self.current_block()
        if not b or self.restoring or b['type']!='dialogue':return
        selected=self.speaker_combo.currentData();self.default_speaker=selected;self.mutate('Change speaker',lambda:b.update(speaker=selected))
    def cast_clicked(self,item):
        ident=item.data(Qt.ItemDataRole.UserRole);self.default_speaker=ident;self.character_state();b=self.current_block()
        if b and b['type']=='dialogue':self.mutate('Choose speaker',lambda:b.update(speaker=ident))
        else:self.statusBar().showMessage('Next dialogue speaker: '+self.speaker_name(ident),5000)
    def chosen_character(self):
        item=self.cast.currentItem();return self.character(item.data(Qt.ItemDataRole.UserRole)) if item else None
    def character_state(self):
        c=self.chosen_character();self.edit_character_button.setEnabled(c is not None);self.remove_character_button.setEnabled(c is not None);self.character_description.setText(c.get('description','') if c else '')
    def add_character(self):
        dialog=CharacterDialog(self)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        c=dialog.character;self.default_speaker=c['id'];self.mutate('Add character',lambda:self.project['characters'].append(c))
    def edit_character(self):
        c=self.chosen_character()
        if not c:return
        dialog=CharacterDialog(self,c)
        if dialog.exec()==QDialog.DialogCode.Accepted:self.mutate('Edit character',lambda:c.update(dialog.character))
    def remove_character(self):
        c=self.chosen_character()
        if not c:return
        affected=[b for b in self.project['blocks'] if b.get('speaker')==c['id']];replacement=None
        if affected:
            others=[p for p in self.project['characters'] if p['id']!=c['id']];labels=['Leave these dialogues unassigned']+[f"{i+1}. {p['name']}" for i,p in enumerate(others)]
            choice,ok=QInputDialog.getItem(self,'Reassign dialogue',f"{c['name']} speaks in {len(affected)} block(s). Keep their text and reassign to:",labels,0,False)
            if not ok:return
            index=labels.index(choice);replacement=others[index-1]['id'] if index else None
        elif QMessageBox.question(self,'Remove character',f"Remove {c['name']} from this cast?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        def change():
            self.project['characters'].remove(c)
            for b in affected:b['speaker']=replacement
        if self.default_speaker==c['id']:self.default_speaker=replacement
        self.mutate('Remove character',change)
    def filter_cast(self,*_):
        search=self.cast_search.text().casefold()
        for i in range(self.cast.count()):
            item=self.cast.item(i);c=self.character(item.data(Qt.ItemDataRole.UserRole));item.setHidden(search not in (c['name']+' '+c.get('description','')).casefold())
    def filter_blocks(self,*_):
        # A block is hidden if it fails the search, the tag filter or the outline switch.
        search=self.block_search.text().casefold();tag=self.tag_filter.currentData();outline=self.outline_button.isChecked()
        for i in range(self.blocks.count()):
            item=self.blocks.item(i);b=next((b for b in self.project['blocks'] if b['id']==item.data(Qt.ItemDataRole.UserRole)),None)
            if b:
                words=(self.speaker_name(b.get('speaker'))+' '+b['text']+' '+b.get('delivery','')+' '+' '.join(b.get('tags',[]))+' '+b['type']).casefold()
                item.setHidden(search not in words or bool(tag and tag not in b.get('tags',[])) or (outline and b['type']!='scene'))
        filtering=bool(search or tag or outline);self.blocks.setDragEnabled(not filtering);self.blocks.setAcceptDrops(not filtering)
    def ask_save(self):
        self.wait_jobs()
        if not self.dirty():return True
        result=QMessageBox.question(self,'Unsaved script','Save your script before continuing?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Save)
        if result==QMessageBox.StandardButton.Cancel:return False
        if result==QMessageBox.StandardButton.Discard:return True
        if not self.save():return False
        self.wait_jobs();return self.save_success and not self.dirty()
    def install_project(self,data,path='',recovered=False):
        self.wait_jobs();self.remove_recovery();self.project=validate(copy.deepcopy(data));self.path=path;self.selected=self.project['blocks'][0]['id'] if self.project['blocks'] else None;self.default_speaker=None;self.recovered_dirty=recovered;self.history.clear();self.history.setClean();self.revision+=1;self.cast_search.clear();self.block_search.clear();self.refresh()
    def new(self):
        if self.ask_save():self.install_project(new_project());self.statusBar().showMessage('New script. Add your cast pictures to get started.')
    def open_dialog(self):
        path,_=QFileDialog.getOpenFileName(self,'Open script',self.settings.value('last_directory',''),FILTER)
        if path:self.open_path(path)
    def open_path(self,path):
        try:
            with open(path,encoding='utf-8') as f:data=validate(json.load(f))
        except Exception as e:QMessageBox.critical(self,'Cannot open script',str(e));return False
        if not self.ask_save():return False
        # Saving in the prompt may have changed this same file. Re-read it.
        try:
            with open(path,encoding='utf-8') as f:data=validate(json.load(f))
        except Exception as e:QMessageBox.critical(self,'Cannot open script',str(e));return False
        self.install_project(data,os.path.abspath(path));self.remember(path);self.statusBar().showMessage('Opened '+os.path.basename(path));return True
    def save(self):return self.request_save(self.path) if self.path else self.save_as()
    def save_as(self):
        path,_=QFileDialog.getSaveFileName(self,'Save script',self.path or os.path.join(self.settings.value('last_directory',''),(self.project['title'].strip() or 'Untitled')+'.scriptstudio'),FILTER)
        if not path:return False
        if not path.lower().endswith('.scriptstudio'):path+='.scriptstudio'
        return self.request_save(path)
    def request_save(self,path):
        if self.saving:self.statusBar().showMessage('Saving is already in progress.');return False
        if not path:return False
        path=os.path.abspath(path);data=copy.deepcopy(self.project);context={'kind':'save','path':path,'revision':self.revision,'data':data};job=WriteJob(path,data,context);job.signals.done.connect(self.job_done);self.jobs.append(job);self.saving=True;self.save_success=False;self.save_action.setEnabled(False);self.saveas_action.setEnabled(False);self.statusBar().showMessage('Saving…');self.pool.start(job);return True
    def job_done(self,context,error):
        self.jobs=[j for j in self.jobs if j.context is not context]
        if context['kind']=='save':
            self.saving=False;self.save_success=not error;self.save_action.setEnabled(True);self.saveas_action.setEnabled(True)
            if error:QMessageBox.critical(self,'Save failed','Your edits are still here.\n'+error);self.statusBar().showMessage('Save failed — edits remain unsaved.');return
            self.path=context['path'];self.remember(self.path)
            if context['revision']==self.revision and self.project==context['data']:
                self.history.setClean();self.recovered_dirty=False;self.remove_recovery();self.statusBar().showMessage('Script saved. Pictures are embedded in this project.')
            else:
                self.recovered_dirty=True;self.statusBar().showMessage('Snapshot saved. Newer edits still need Ctrl+S.')
            self.update_title()
        else:
            self.recovery_busy=False;self.recovery_label.setText('Recovery saved' if not error else 'Recovery failed')
            if error:self.statusBar().showMessage('Recovery failed: '+error)
    def wait_jobs(self):
        while self.saving or self.recovery_busy:QApplication.processEvents();time.sleep(.005)
    def autosave(self):
        if not self.dirty() or self.recovery_busy or self.saving:return False
        data={'format':'ScriptStudioRecovery','saved_at':time.time(),'original_path':self.path,'project':copy.deepcopy(self.project),'selected':self.selected};job=WriteJob(str(self.recovery_file),data,{'kind':'recovery'});job.signals.done.connect(self.job_done);self.jobs.append(job);self.recovery_busy=True;self.pool.start(job);return True
    def remove_recovery(self):
        try:self.recovery_file.unlink(missing_ok=True)
        except OSError:pass
    def recovery_candidates(self):
        candidates=[]
        for path in self.recovery_file.parent.glob('session-*.json'):
            if path==self.recovery_file:continue
            try:
                data=json.loads(path.read_text(encoding='utf-8'));validate(data['project']);original=data.get('original_path','')
                if original and os.path.exists(original) and os.path.getmtime(original)>=data.get('saved_at',0):continue
                candidates.append((path,data))
            except (OSError,ValueError,KeyError,TypeError):continue
        return sorted(candidates,key=lambda item:item[1].get('saved_at',0),reverse=True)
    def offer_recovery(self):
        if self.recovery_candidates() and QMessageBox.question(self,'Recover interrupted work','A recovery copy from an earlier session is available. Open recovery choices?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.Yes)==QMessageBox.StandardButton.Yes:self.recover_dialog()
    def recover_dialog(self):
        items=self.recovery_candidates()
        if self.recovery_file.exists():
            try:items.insert(0,(self.recovery_file,json.loads(self.recovery_file.read_text(encoding='utf-8'))))
            except (OSError,ValueError):pass
        if not items:QMessageBox.information(self,'Recovery','No unsaved recovery copies are available. Recovery runs every 30 seconds while there are unsaved edits.');return
        labels=[f"{i+1}. {data['project']['title']} — {time.strftime('%Y-%m-%d %H:%M',time.localtime(data.get('saved_at',0)))}" for i,(_,data) in enumerate(items)]
        choice,ok=QInputDialog.getItem(self,'Recover script','Choose interrupted work:',labels,0,False)
        if not ok or not self.ask_save():return
        source,data=items[labels.index(choice)];self.install_project(data['project'],data.get('original_path',''),True);self.selected=data.get('selected');self.refresh();self.autosave();self.wait_jobs()
        # Keep the previous recovery if writing the new session copy failed.
        transfer_ok=False
        try:transfer_ok=json.loads(self.recovery_file.read_text(encoding='utf-8')).get('project')==self.project
        except (OSError,ValueError):pass
        if source!=self.recovery_file and transfer_ok:
            try:source.unlink()
            except OSError:pass
        self.statusBar().showMessage('Recovered script. Use Ctrl+S to save it.');self.update_title()
    def remember(self,path):
        path=os.path.abspath(path);recent=self.settings.value('recent',[],type=list);recent=[p for p in recent if os.path.normcase(p)!=os.path.normcase(path)];self.settings.setValue('recent',[path]+recent[:9]);self.settings.setValue('last_directory',os.path.dirname(path));self.settings.sync();self.update_recent()
    def update_recent(self):
        self.recent.clear();paths=[p for p in self.settings.value('recent',[],type=list) if os.path.isfile(p)][:10];self.settings.setValue('recent',paths)
        if not paths:
            a=self.recent.addAction('No recent projects');a.setEnabled(False)
        for p in paths:
            a=self.recent.addAction(os.path.basename(p));a.setToolTip(p);a.triggered.connect(lambda checked=False,path=p:self.open_path(path))
        self.recent.addSeparator();a=self.recent.addAction('Clear recent list');a.triggered.connect(lambda:(self.settings.setValue('recent',[]),self.update_recent()))
    def tag_line(self,b):
        # Tags only reach exports when "Include tags in exports" is ticked.
        return '[tags: '+', '.join(b['tags'])+']' if b.get('tags') and self.settings.value('export_tags',False,type=bool) else ''
    def plain_text(self):
        lines=[self.project['title'].strip() or 'Untitled','='*40,'']
        for b in self.project['blocks']:
            if b['type']=='note':continue
            if b['type']=='scene':lines.append(b['text'].upper())
            elif b['type']=='action':lines.append(b['text'])
            else:
                lines.append(self.speaker_name(b.get('speaker')).upper())
                if b.get('delivery'):lines.append('('+b['delivery']+')')
                lines.append(b['text'])
            tags=self.tag_line(b)
            if tags:lines.append(tags)
            lines.append('')
        return '\n'.join(lines)
    def export_pdf(self,path):
        esc=lambda text:html.escape(text).replace('\n','<br>')
        paragraphs=['<h1>'+esc(self.project['title'].strip() or 'Untitled')+'</h1>']
        for b in self.project['blocks']:
            if b['type']=='note':continue
            if b['type']=='scene':paragraphs.append('<h2>'+esc(b['text'].upper())+'</h2>')
            elif b['type']=='action':paragraphs.append('<p>'+esc(b['text'])+'</p>')
            else:
                heading=esc(self.speaker_name(b.get('speaker')).upper())
                if b.get('delivery'):heading+='<br><i>('+esc(b['delivery'])+')</i>'
                paragraphs.append('<p style="margin-left:65px; margin-right:65px;"><b>'+heading+'</b><br>'+esc(b['text'])+'</p>')
            tags=self.tag_line(b)
            if tags:paragraphs.append('<p><i>'+esc(tags)+'</i></p>')
        doc=QTextDocument();doc.setDefaultFont(QFont('DejaVu Sans Mono',11));doc.setHtml('<html><body style="color:#111;background:white;">'+''.join(paragraphs)+'</body></html>')
        printer=QPrinter(QPrinter.PrinterMode.HighResolution);printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat);printer.setOutputFileName(path);printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4));doc.print_(printer)
        if not os.path.isfile(path) or os.path.getsize(path)<200:raise OSError('PDF could not be created.')
    def storyboard_data(self):
        # One blank storyboard panel per action/dialogue. Scene headings label
        # subsequent panels; this is an editable handoff, not live syncing.
        groups=[];scene='Scene 1';notes=[]
        for b in self.project['blocks']:
            if b['type']=='note':continue
            if b['type']=='scene':
                if notes:groups.append((scene,'\n\n'.join(notes)));notes=[]
                scene=b['text'] or 'Untitled scene'
            else:
                text=b['text']
                if b['type']=='dialogue':text=self.speaker_name(b.get('speaker')).upper()+((' ('+b['delivery']+')') if b.get('delivery') else '')+'\n'+text
                groups.append((scene,text+(('\n'+self.tag_line(b)) if self.tag_line(b) else '')))
        if not groups:groups=[(scene,'')]
        image=QImage(1920,1080,QImage.Format.Format_ARGB32);image.fill(Qt.GlobalColor.white);buf=QBuffer();buf.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buf,'PNG');encoded=base64.b64encode(bytes(buf.data())).decode('ascii')
        panels=[{'image':encoded,'notes':note,'duration':2.0,'scene':scene,'shot_label':str(i+1),'background':'white','source_path':'','underlay':''} for i,(scene,note) in enumerate(groups)]
        return {'version':1,'title':self.project['title'],'canvas_w':1920,'canvas_h':1080,'aspect':'16:9','fps':24,'markers':[],'audio':'','panels':panels}
    def export_dialog(self,kind):
        filters={'txt':'Text (*.txt)','pdf':'PDF (*.pdf)','sboard':'StoryboardStudio (*.sboard)'};path,_=QFileDialog.getSaveFileName(self,'Export script',os.path.join(self.settings.value('last_directory',''),'Script.'+kind),filters[kind])
        if not path:return
        if not path.lower().endswith('.'+kind):path+='.'+kind
        try:
            if kind=='txt':Path(path).write_text(self.plain_text(),encoding='utf-8')
            elif kind=='pdf':self.export_pdf(path)
            else:atomic_json(path,self.storyboard_data())
            self.statusBar().showMessage('Exported '+os.path.basename(path),8000)
        except Exception as e:QMessageBox.critical(self,'Export failed',str(e))
    def save_workspace(self):
        self.settings.setValue('geometry',self.saveGeometry());self.settings.setValue('splitter',self.splitter.saveState());self.settings.sync()
    def restore_workspace(self):
        geometry=self.settings.value('geometry');splitter=self.settings.value('splitter')
        if geometry:self.restoreGeometry(geometry)
        if splitter:self.splitter.restoreState(splitter)
    def reset_workspace(self):self.resize(1220,810);self.splitter.setSizes([235,450,450])
    def help(self):QMessageBox.information(self,'ScriptStudio — quick start','1. Add a character: picture, name, optional description.\n2. Add a scene, action or dialogue block.\n3. Click a cast picture to choose who is talking.\n4. Write in the right-hand editor. Reorder blocks with arrows or drag.\n\nCtrl+S: Save | Ctrl+Shift+S: Save As\nCtrl+O: Open | Ctrl+N: New\nCtrl+Z: Undo | Ctrl+Y / Ctrl+Shift+Z: Redo\nCtrl+D: Duplicate block | F2: Rename scene | Ctrl+H: Find and replace | Ctrl+E: PDF export\n\nTags: pick a preset or type your own, then click a tag to remove it.\n\nCharacters are linked by ID; renaming updates their dialogue. Pictures are embedded in .scriptstudio projects. Recovery runs every 30 seconds.\n\nExport > StoryboardStudio creates blank panels with script text as notes. This is a one-way export, not live syncing.')
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls() and any(u.toLocalFile().lower().endswith('.scriptstudio') for u in event.mimeData().urls()):event.acceptProposedAction()
    def dropEvent(self,event):
        paths=[u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith('.scriptstudio')]
        if paths:self.open_path(paths[0]);event.acceptProposedAction()
    def closeEvent(self,event):
        if not self.ask_save():event.ignore();return
        self.timer.stop();self.wait_jobs();self.remove_recovery();self.save_workspace();event.accept()
def main():
    if sys.platform=='win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ScriptStudio.DarkCherry')
        except OSError:pass
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar,True)
    app=QApplication(sys.argv);app.setApplicationName('ScriptStudio');app.setOrganizationName('ScriptStudio');app.setStyle('Fusion');app.setStyleSheet(STYLE)
    root=getattr(sys,'_MEIPASS',os.path.dirname(os.path.abspath(__file__)));app.setWindowIcon(QIcon(os.path.join(root,'app.ico')))
    win=Window();win.setWindowIcon(app.windowIcon());win.show()
    if len(sys.argv)>1 and sys.argv[1].lower().endswith('.scriptstudio'):win.open_path(sys.argv[1])
    return app.exec()
if __name__=='__main__':raise SystemExit(main())
