import csv
import ctypes
import ctypes.wintypes
import os
import re
import sqlite3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

CSV_PATH = Path(os.environ.get('ECDICT_CSV', Path(__file__).with_name('stardict.csv')))
DB_PATH = CSV_PATH.with_name('ecdict_lookup.sqlite3')
HOTKEY_SEARCH, WM_HOTKEY = 0x4A21, 0x0312
MOD_ALT, MOD_CONTROL = 0x0001, 0x0002
VK_Q = 0x51


def words_in(text):
    text = text.replace('\u00ad', '').replace('\u2010', '-').replace('\u2011', '-')
    text = re.sub(r'(?<=\w)-\s+(?=[a-z])', '', text, flags=re.I)
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text)


def build_index(status):
    if DB_PATH.exists() and DB_PATH.stat().st_mtime >= CSV_PATH.stat().st_mtime:
        return
    status('首次建立本地词典索引…')
    tmp = DB_PATH.with_suffix('.tmp')
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.execute('CREATE TABLE words(word TEXT PRIMARY KEY COLLATE NOCASE, phonetic TEXT, pos TEXT, translation TEXT, definition TEXT)')
    batch=[]
    with CSV_PATH.open('r', encoding='utf-8-sig', newline='', errors='replace') as f:
        for row in csv.DictReader(f):
            word=(row.get('word') or '').strip()
            if word: batch.append((word,row.get('phonetic') or '',row.get('pos') or '',row.get('translation') or '',row.get('definition') or ''))
            if len(batch)>=5000:
                con.executemany('INSERT OR REPLACE INTO words VALUES(?,?,?,?,?)',batch); con.commit(); batch.clear()
    if batch: con.executemany('INSERT OR REPLACE INTO words VALUES(?,?,?,?,?)',batch)
    con.commit(); con.close(); tmp.replace(DB_PATH)


class App:
    def __init__(self, root):
        self.root=root; root.title('PDF 生词速查 · 离线词典'); root.geometry('430x390+80+100'); root.attributes('-topmost',True)
        self.status=tk.StringVar(value='正在加载本地词典…'); self.query=tk.StringVar(); self.db=None; self.after_id=None
        ttk.Label(root,text='PDF 生词速查',font=('Segoe UI',14,'bold')).pack(anchor='w',padx=12,pady=(10,2))
        ttk.Label(root,text='PDF 中选词并复制，词典自动查；Ctrl+Alt+Q 调出查词框').pack(anchor='w',padx=12)
        row=ttk.Frame(root); row.pack(fill='x',padx=12,pady=8)
        self.entry=ttk.Entry(row,textvariable=self.query,font=('Segoe UI',13)); self.entry.pack(fill='x',expand=True)
        self.query.trace_add('write',self.schedule_lookup)
        self.out=tk.Text(root,wrap='word',font=('Segoe UI',11),height=12); self.out.pack(fill='both',expand=True,padx=12,pady=(0,8))
        ttk.Label(root,textvariable=self.status).pack(anchor='w',padx=12,pady=(0,8))
        self.user32=ctypes.windll.user32
        self.hotkey_search=self.user32.RegisterHotKey(None,HOTKEY_SEARCH,MOD_CONTROL|MOD_ALT,VK_Q)
        self.clipboard_sequence=self.user32.GetClipboardSequenceNumber()
        threading.Thread(target=self.init_index,daemon=True).start(); self.poll_hotkeys()
        root.protocol('WM_DELETE_WINDOW',self.close)

    def set_status(self,text): self.root.after(0,self.status.set,text)
    def init_index(self):
        try:
            build_index(self.set_status); self.db=sqlite3.connect(DB_PATH,check_same_thread=False)
            self.set_status('就绪：在 PDF 里选词并复制，剪贴板变化后自动查询。')
        except Exception as e: self.set_status(f'词典加载失败：{e}')

    def poll_hotkeys(self):
        msg=ctypes.wintypes.MSG()
        while self.user32.PeekMessageW(ctypes.byref(msg),None,WM_HOTKEY,WM_HOTKEY,1):
            if msg.wParam==HOTKEY_SEARCH:
                self.root.deiconify(); self.root.lift(); self.entry.focus_set(); self.entry.selection_range(0,'end')
        seq=self.user32.GetClipboardSequenceNumber()
        if seq != self.clipboard_sequence:
            self.clipboard_sequence=seq
            self.root.after(120,self.read_clipboard)
        self.root.after(80,self.poll_hotkeys)

    def read_clipboard(self):
        try:
            text=self.root.clipboard_get().strip()
            if not text: self.status.set('剪贴板没有文本；确认 PDF 中已选中文字，再按 Ctrl+C。'); return
            ws=words_in(text); self.query.set(' '.join(ws) if ws else text)
            self.root.deiconify(); self.root.lift(); self.status.set('已读取并自动查询。')
        except tk.TclError: self.status.set('没有读到剪贴板文本，请重新选择并复制。')

    def schedule_lookup(self,*_):
        if self.after_id: self.root.after_cancel(self.after_id)
        self.after_id=self.root.after(160,self.lookup)

    def lookup(self):
        self.after_id=None
        if self.db is None: return
        text=self.query.get().strip()
        if not text: self.out.delete('1.0','end'); return
        ws=words_in(text); phrase=' '.join(ws) if ws else text
        row=self.db.execute('SELECT word,phonetic,pos,translation,definition FROM words WHERE word=? COLLATE NOCASE',(phrase,)).fetchone()
        self.out.delete('1.0','end')
        if row:
            self.show_row(row); self.status.set('完整词条 · 本地离线查询'); return
        if len(ws)>1:
            rows=[]
            for w in ws:
                found=self.db.execute('SELECT word,phonetic,pos,translation,definition FROM words WHERE word=? COLLATE NOCASE',(w,)).fetchone()
                if found: rows.append(found)
            if rows:
                for item in rows: self.show_row(item); self.out.insert('end','\n\n')
                self.status.set('未找到完整词组，列出词组内单词释义。'); return
        row=self.db.execute('SELECT word,phonetic,pos,translation,definition FROM words WHERE word=? COLLATE NOCASE',(phrase,)).fetchone()
        if not row:
            row=self.db.execute('SELECT word,phonetic,pos,translation,definition FROM words WHERE word LIKE ? COLLATE NOCASE ORDER BY length(word) LIMIT 1',(phrase+'%',)).fetchone()
        if row: self.show_row(row); self.status.set('本地离线查询')
        else: self.out.insert('end',f'词库未收录：{phrase}'); self.status.set('未找到')

    def show_row(self,row):
        word,phonetic,pos,translation,definition=row
        self.out.insert('end',f'{word} {phonetic}\n{pos}\n{translation}\n{definition}')

    def close(self):
        self.user32.UnregisterHotKey(None,HOTKEY_SEARCH); self.root.destroy()


if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
