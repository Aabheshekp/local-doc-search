from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT=Path(__file__).parent; DB=ROOT/'library.sqlite3'
def conn():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 with conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
  c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(title,body,content="documents",content_rowid="id")')
  c.executescript("CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN INSERT INTO documents_fts(rowid,title,body) VALUES(new.id,new.title,new.body); END; CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN INSERT INTO documents_fts(documents_fts,rowid,title,body) VALUES('delete',old.id,old.title,old.body); END; CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN INSERT INTO documents_fts(documents_fts,rowid,title,body) VALUES('delete',old.id,old.title,old.body); INSERT INTO documents_fts(rowid,title,body) VALUES(new.id,new.title,new.body); END;")
@asynccontextmanager
async def lifespan(app): init();yield
app=FastAPI(title='Local Document Search',version='1.0.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
class DocumentIn(BaseModel): title:str=Field(min_length=1,max_length=160);body:str=Field(min_length=1,max_length=20000)
@app.get('/')
def home():return FileResponse(ROOT/'static'/'index.html')
@app.get('/api/documents')
def search(q:str=''):
 with conn() as c:
  if not q.strip(): rows=c.execute('SELECT id,title,substr(body,1,180) AS excerpt,created_at FROM documents ORDER BY id DESC LIMIT 100').fetchall()
  else:
   tokens=[t for t in q.split() if t.isalnum()]
   if not tokens:return []
   query=' AND '.join('"'+t+'"' for t in tokens)
   try: rows=c.execute('SELECT d.id,d.title,snippet(documents_fts,1,"","…",0) AS excerpt,d.created_at FROM documents_fts JOIN documents d ON d.id=documents_fts.rowid WHERE documents_fts MATCH ? ORDER BY rank LIMIT 100',(query,)).fetchall()
   except sqlite3.OperationalError: return []
 return [dict(r) for r in rows]
@app.post('/api/documents',status_code=201)
def create(doc:DocumentIn):
 with conn() as c:cur=c.execute('INSERT INTO documents(title,body) VALUES(?,?)',(doc.title.strip(),doc.body.strip()));return {'id':cur.lastrowid,'title':doc.title.strip()}
@app.get('/api/documents/{doc_id}')
def get_document(doc_id:int):
 with conn() as c:r=c.execute('SELECT * FROM documents WHERE id=?',(doc_id,)).fetchone()
 if not r:raise HTTPException(404,'Document not found')
 return dict(r)
