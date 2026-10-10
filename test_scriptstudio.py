import os,sys,tempfile,json,base64,time,copy,importlib.util
from pathlib import Path
from unittest.mock import patch
root=Path(tempfile.mkdtemp(prefix='scriptstudio-tests-'));os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['SS_SETTINGS_FILE']=str(root/'settings.ini');os.environ['SS_RECOVERY_DIR']=str(root/'recovery')
sys.path.insert(0,str(Path(__file__).parent))
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog,QDialog,QInputDialog
from PySide6.QtCore import Qt,QTimer,QPoint,QModelIndex
from PySide6.QtGui import QImage,QColor
from PySide6.QtTest import QTest
from scriptstudio import Window,STYLE,image_data,new_block,new_project,validate,atomic_json,WriteJob,CharacterDialog
config=Path.cwd()/(root.name+'-screen.json');config.write_text(json.dumps({'screens':[{'name':'Test','x':0,'y':0,'width':1600,'height':1000}]}));app=QApplication(['test','-platform','offscreen:configfile='+config.name]);config.unlink();app.setStyle('Fusion');app.setStyleSheet(STYLE)
errors=[]
def hook(t,v,tb):
    import traceback
    errors.append(str(v));traceback.print_exception(t,v,tb)
sys.excepthook=hook
checks=0
def check(label,condition):
    global checks
    assert condition,label
    checks+=1;print('[PASS]',label,flush=True)
def wait(predicate,timeout=15):
    end=time.monotonic()+timeout
    while not predicate() and time.monotonic()<end:QTest.qWait(10)
    assert predicate(),'Timed out'
w=Window(False);w.show();w.timer.stop();QTest.qWait(90)
check('Application opens in dark cherry theme',w.isVisible() and '#190f15' in STYLE and '#f8eaf0' in STYLE)
check('New script starts with a scene',len(w.project['blocks'])==1 and w.current_block()['type']=='scene')
check('New script starts clean',not w.dirty())
# Upload a real local image, embed it, then remove the source.
im=QImage(90,90,QImage.Format.Format_ARGB32);im.fill(QColor('#ab305a'));photo=root/'photo.png';im.save(str(photo));encoded=image_data(photo)
c1={'id':'maya','name':'Maya','description':'The patient friend','image':encoded};c2={'id':'jules','name':'Jules','description':'Quick to laugh','image':encoded}
def accept_character(dialog):dialog.character=copy.deepcopy(c1);return QDialog.DialogCode.Accepted
with patch.object(CharacterDialog,'exec',accept_character):w.add_character()
check('Character add UI embeds a named image',w.project['characters'][0]==c1 and w.default_speaker=='maya')
w.mutate('Add second character',lambda:w.project['characters'].append(copy.deepcopy(c2)))
check('Character cards display pictures and names',w.cast.count()==2 and not w.cast.item(0).icon().isNull())
photo.unlink();check('Embedded picture survives source deletion',not QImage.fromData(base64.b64decode(w.project['characters'][0]['image'])).isNull())
# Buttons and selector.
w.cast.itemClicked.emit(w.cast.item(0));w.add_block('dialogue');dialogue=w.current_block()
check('Cast click selects next dialogue speaker',dialogue['speaker']=='maya')
w.text.setPlainText('Are you still awake?');w.delivery.setText('whispering')
check('Writing changes the selected dialogue and delivery',w.current_block()['text']=='Are you still awake?' and w.current_block()['delivery']=='whispering')
w.cast.itemClicked.emit(w.cast.item(1));check('Clicking another picture reassigns dialogue',w.current_block()['speaker']=='jules')
check('Picture picker and speaker combo agree',w.speaker_combo.currentData()=='jules')
w.undo();check('Undo restores previous speaker',w.current_block()['speaker']=='maya')
w.redo();check('Redo restores reassigned speaker',w.current_block()['speaker']=='jules')
w.speaker_combo.setCurrentIndex(w.speaker_combo.findData('maya'));check('Combo changes speaker too',w.current_block()['speaker']=='maya')
# Actual keyboard typing and global undo.
w.text.setFocus();w.text.selectAll();QTest.keyClicks(w.text,'Hello there.');check('Keyboard typing updates model',w.current_block()['text']=='Hello there.')
QTest.keyClick(w.text,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier);check('Ctrl+Z works while typing in editor',w.current_block()['text']!='Hello there.')
QTest.keyClick(w.text,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier);check('Ctrl+Y restores typed text',w.current_block()['text']=='Hello there.')
# Rename by character dialog; previously assigned dialogues update by ID.
w.cast.setCurrentRow(0)
def accept_edit(dialog):dialog.character['name']='Maya Renamed';return QDialog.DialogCode.Accepted
with patch.object(CharacterDialog,'exec',accept_edit):w.edit_character()
check('Character rename keeps dialogue ID',w.current_block()['speaker']=='maya' and 'MAYA RENAMED' in w.plain_text())
check('Rename updates list preview',w.blocks.currentItem().text().startswith('MAYA RENAMED'))
w.undo();check('Undo character rename updates dialogue names',w.speaker_name('maya')=='Maya')
w.redo();check('Redo character rename updates dialogue names',w.speaker_name('maya')=='Maya Renamed')
# Search and block operations.
w.cast_search.setText('patient');check('Character search uses descriptions',not w.cast.item(0).isHidden() and w.cast.item(1).isHidden());w.cast_search.clear()
w.block_search.setText('maya renamed');check('Script search finds speakers',not w.blocks.item(1).isHidden() and w.blocks.item(0).isHidden());w.block_search.clear()
oldid=w.selected;n=len(w.project['blocks']);w.duplicate_block();check('Duplicate preserves dialogue but gets a unique ID',len(w.project['blocks'])==n+1 and w.selected!=oldid and w.current_block()['speaker']=='maya')
newid=w.selected;w.move_block(-1);check('Move up changes block order',w.project['blocks'][1]['id']==newid);w.undo();check('Undo restores order',w.project['blocks'][2]['id']==newid);w.redo();check('Redo reapplies order',w.project['blocks'][1]['id']==newid)
# Actual model rowsMoved path for drag and drop.
ids=[b['id'] for b in w.project['blocks']]
check('Qt drag model accepts a move',w.blocks.model().moveRows(QModelIndex(),1,1,QModelIndex(),3))
check('Dragging synchronizes data order',[b['id'] for b in w.project['blocks']]==[ids[0],ids[2],ids[1]])
w.undo();check('Undo drag restores order',[b['id'] for b in w.project['blocks']]==ids)
w.redo();check('Redo drag restores dropped order',[b['id'] for b in w.project['blocks']]==[ids[0],ids[2],ids[1]])
with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):w.delete_block()
check('Delete block works and preserves other blocks',len(w.project['blocks'])==2);w.undo();check('Undo restores deleted block',len(w.project['blocks'])==3)
w.add_block('action');w.text.setPlainText('The cherry-red lamp flickers.');check('Action has no speaker controls',w.current_block()['speaker'] is None and not w.speaker_combo.isVisible())
w.add_block('scene');w.text.setPlainText('Scene 2 — Garden, dawn');check('Scene headings have their own type',w.current_block()['type']=='scene')
w.type_combo.setCurrentIndex(w.type_combo.findData('dialogue'));check('Block type can be changed',w.current_block()['type']=='dialogue' and w.speaker_combo.isVisible())
w.undo();check('Undo restores prior block type',w.current_block()['type']=='scene')
# Character removal preserves dialogue and supports reassignment.
w.cast.setCurrentRow(0);prior=len(w.project['blocks']);texts=[b['text'] for b in w.project['blocks']]
with patch.object(QInputDialog,'getItem',return_value=('1. Jules',True)):w.remove_character()
check('Removing cast member reassigns every dialogue',all(b.get('speaker')!='maya' for b in w.project['blocks']) and not w.character('maya'))
check('Character removal never deletes dialogue text',len(w.project['blocks'])==prior and [b['text'] for b in w.project['blocks']]==texts)
w.undo();check('Undo restores removed character and associations',w.character('maya') is not None and any(b.get('speaker')=='maya' for b in w.project['blocks']))
# Dialog input validation and image upload.
d=CharacterDialog(w)
d.accept();check('Character dialog requires a name',bool(d.error.text()) and d.result()!=QDialog.DialogCode.Accepted)
im.save(str(photo))
with patch.object(QFileDialog,'getOpenFileName',return_value=(str(photo),'')):d.choose()
check('Choose-picture dialog embeds an image',bool(d.character['image']))
d.name.setText('A third character');d.accept();check('Named character dialog accepts',d.result()==QDialog.DialogCode.Accepted);d.close()
# Save and reopening from the actual file.
w.title_edit.setText('Cherry Nights');path=root/'Cherry Nights.scriptstudio'
with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'')):check('Save As starts background write',w.save_as())
wait(lambda:not w.saving)
check('Save produces a self-contained project',validate(json.loads(path.read_text(encoding='utf-8')))==w.project)
check('Successful save clears dirty flag',w.save_success and not w.dirty())
check('Recent projects remembers saved file',w.settings.value('recent',[],type=list)[0]==str(path))
expected=copy.deepcopy(w.project);w.new();check('New replaces clean script',len(w.project['characters'])==0)
w.recent.actions()[0].trigger();app.processEvents();check('Recent project action reopens everything',w.project==expected and w.path==str(path))
# Asynchronous saving must not mark later edits as saved.
b=w.current_block();w.text.setPlainText('Snapshot text');original_run=WriteJob.run

def slow(job):time.sleep(.15);original_run(job)
ticks=[];timer=QTimer();timer.setInterval(5);timer.timeout.connect(lambda:ticks.append(1));timer.start()
with patch.object(WriteJob,'run',slow):
    w.save();QTest.qWait(40);w.text.setPlainText('Newer unsaved text');wait(lambda:not w.saving)
timer.stop();check('GUI remains responsive during background save',len(ticks)>8)
check('Saved file is a consistent snapshot',json.loads(path.read_text(encoding='utf-8'))['blocks'][0]['text']=='Snapshot text')
check('Later edits stay dirty after background saving',w.dirty() and w.current_block()['text']=='Newer unsaved text')
w.save();wait(lambda:not w.saving);check('Next Save persists later edits',not w.dirty() and json.loads(path.read_text(encoding='utf-8'))['blocks'][0]['text']=='Newer unsaved text')
# Failure preserves both previous file and live edits.
w.text.setPlainText('Preserve me');previous=path.read_bytes();reports=[]
with patch('scriptstudio.atomic_json',side_effect=OSError('Test disk failure')),patch.object(QMessageBox,'critical',side_effect=lambda *args:reports.append(args)):
    w.save();wait(lambda:not w.saving)
check('Save failure preserves previous file',path.read_bytes()==previous)
check('Save failure preserves edits and reports error',w.dirty() and w.current_block()['text']=='Preserve me' and len(reports)==1)
# Save/Discard/Cancel prompts.
with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel):
    live=w.project;w.new();check('Cancel prevents new project from losing work',w.project is live)
    check('Cancel prevents opening another project',not w.open_path(str(path)) and w.project is live)
    w.close();check('Cancel prevents closing unsaved work',w.isVisible())
with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save):
    check('Save before open waits for successful write',w.open_path(str(path)))
check('Save-before-open persists edits',w.current_block()['text']=='Preserve me' and not w.dirty())
# Project validation prevents a damaged load from replacing the current document.
invalid=root/'broken.scriptstudio';invalid.write_text('{broken');reports=[]
with patch.object(QMessageBox,'critical',side_effect=lambda *args:reports.append(args)):
    current=w.project;check('Malformed files are rejected',not w.open_path(str(invalid)) and w.project is current and len(reports)==1)
# Export text and PDF via dialog; PDF has script text but no character art.
w.title_edit.setText('Cherry Nights');w.add_block('dialogue');w.text.setPlainText('The stars are still here.');w.speaker_combo.setCurrentIndex(w.speaker_combo.findData('maya'));w.delivery.setText('softly')
txt=root/'script.txt';pdf=root/'script.pdf';sboard=root/'script.sboard'
for kind,destination in (('txt',txt),('pdf',pdf),('sboard',sboard)):
    with patch.object(QFileDialog,'getSaveFileName',return_value=(str(destination),'')):w.export_dialog(kind)
    check('Export '+kind+' creates output',destination.is_file() and destination.stat().st_size>200)
check('Text export contains name, delivery and dialogue','MAYA RENAMED\n(softly)\nThe stars are still here.' in txt.read_text(encoding='utf-8'))
check('PDF is a real PDF',pdf.read_bytes().startswith(b'%PDF'))
board=json.loads(sboard.read_text(encoding='utf-8'));check('Storyboard handoff includes blank panels and dialogue notes',board['canvas_w']==1920 and any('The stars are still here.' in p['notes'] for p in board['panels']) and all(p['image'] for p in board['panels']))
check('Export does not clear unsaved edits',w.dirty())
# Autosave/recovery.
check('Background recovery starts',w.autosave());wait(lambda:not w.recovery_busy)
recovery=json.loads(w.recovery_file.read_text(encoding='utf-8'));check('Recovery has full script and embedded images',recovery['project']==w.project and recovery['project']['characters'][0]['image']==encoded)
# Simulate another interrupted session; delete only after verified recovery.
foreign=w.recovery_file.parent/'session-old.json';atomic_json(foreign,recovery)
check('Recovery scanner finds interrupted session',any(p==foreign for p,_ in w.recovery_candidates()))
with patch.object(QInputDialog,'getItem',side_effect=lambda *args:(args[3][-1],True)),patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Discard):w.recover_dialog()
check('Recovery opens as unsaved document',w.dirty() and w.project==recovery['project'])
check('Recovered script can be saved normally',w.save());wait(lambda:not w.saving);check('Saving recovered script clears recovery dirty state',not w.dirty())
# Recent list cap and duplicate handling.
for i in range(12):
    p=root/f'recent-{i}.scriptstudio';p.write_bytes(path.read_bytes());w.remember(str(p))
check('Recent menu is capped at ten',len(w.settings.value('recent',[],type=list))==10)
w.remember(str(p));check('Recent list deduplicates files',len(w.settings.value('recent',[],type=list))==10)
p.unlink();w.update_recent();check('Missing recent files are pruned',str(p) not in w.settings.value('recent',[],type=list))
w.recent.actions()[-1].trigger();check('Clear recent list works',not w.settings.value('recent',[],type=list))
# Workspace roundtrip and laptop layouts.
w.remember(str(path));w.resize(1180,760);w.splitter.setSizes([205,470,480]);QTest.qWait(50);w.save_workspace();sizes=w.splitter.sizes();geometry=w.size();w.close();app.processEvents()
w2=Window(False);w2.show();w2.timer.stop();QTest.qWait(80)
check('Workspace restores window size',w2.size()==geometry)
check('Workspace restores splitter widths',all(abs(a-b)<=3 for a,b in zip(sizes,w2.splitter.sizes())))
check('Recent projects persist across launches',w2.settings.value('recent',[],type=list)==[str(path)])
for width,height in ((1024,700),(1280,800),(1366,768)):
    w2.resize(width,height);QTest.qWait(30);check(f'Layout fits {width}x{height}',w2.width()==width and w2.height()==height and w2.splitter.width()<=width)
check('No unhandled GUI exceptions',not errors)
w2.close();app.processEvents();print(f'ALL {checks} SCRIPTSTUDIO CHECKS PASSED',flush=True)
print('TEST_OUTPUTS='+str(root),flush=True)
