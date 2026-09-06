"""Local incident ledger; evidence attestations, NOT autonomous verification."""
import argparse
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path

GATES = {'original', 'red', 'green', 'deployment'}

def required(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('non-empty string required')
    return value

class Store:
    def __init__(self, path):
        path=Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('''
CREATE TABLE IF NOT EXISTS incidents(id TEXT PRIMARY KEY, scope TEXT NOT NULL, task TEXT NOT NULL, fingerprint TEXT NOT NULL, status TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS open_identity ON incidents(scope,task,fingerprint) WHERE status='open';
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, incident TEXT NOT NULL, kind TEXT NOT NULL, evidence TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
''')
    def close(self): self.db.close()
    def record(self,scope,task,failure,evidence):
        for v in (scope,task,failure,evidence): required(v)
        fingerprint=hashlib.sha256(failure.encode()).hexdigest()
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute("SELECT id FROM incidents WHERE scope=? AND task=? AND fingerprint=? AND status='open'",(scope,task,fingerprint)).fetchone()
            ident=row['id'] if row else uuid.uuid4().hex
            if not row: self.db.execute('INSERT INTO incidents VALUES(?,?,?,?,?)',(ident,scope,task,fingerprint,'open'))
            self.db.execute('INSERT INTO events(incident,kind,evidence) VALUES(?,?,?)',(ident,'detected',evidence))
        return ident
    def show(self,ident):
        row=self.db.execute('SELECT * FROM incidents WHERE id=?',(ident,)).fetchone()
        if row is None: raise ValueError('unknown incident')
        return dict(row)
    def events(self,ident):
        self.show(ident)
        return [dict(r) for r in self.db.execute('SELECT * FROM events WHERE incident=? ORDER BY seq',(ident,))]
    def attest(self,ident,gate,evidence):
        if gate not in GATES: raise ValueError('unknown gate')
        required(evidence)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.show(ident)['status']!='open': raise ValueError('incident closed')
            self.db.execute('INSERT INTO events(incident,kind,evidence) VALUES(?,?,?)',(ident,gate,evidence))
    def finish(self,ident):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.show(ident)['status']!='open': raise ValueError('incident closed')
            missing=GATES-{r['kind'] for r in self.events(ident)}
            if missing: raise ValueError('missing attestations: '+','.join(sorted(missing)))
            self.db.execute("UPDATE incidents SET status='closed' WHERE id=?",(ident,))
            self.db.execute('INSERT INTO events(incident,kind,evidence) VALUES(?,?,?)',(ident,'closed','all required attestations present; content not independently verified'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',required=True)
    sub=p.add_subparsers(dest='cmd',required=True)
    r=sub.add_parser('record')
    for name in ['scope','task','failure','evidence']: r.add_argument('--'+name,required=True)
    for name in ['show','close']:
        sub.add_parser(name).add_argument('id')
    a=sub.add_parser('attest'); a.add_argument('id'); a.add_argument('gate',choices=sorted(GATES)); a.add_argument('--evidence',required=True)
    args=p.parse_args(); s=Store(args.db)
    try:
        if args.cmd=='record': result={'id':s.record(args.scope,args.task,args.failure,args.evidence)}
        elif args.cmd=='attest': s.attest(args.id,args.gate,args.evidence); result=s.show(args.id)
        elif args.cmd=='close': s.finish(args.id); result=s.show(args.id)
        else: result={**s.show(args.id),'events':s.events(args.id)}
        print(json.dumps(result,ensure_ascii=False))
    except ValueError as e:
        print(json.dumps({'error':str(e)})); return 2
    finally: s.close()
    return 0

if __name__=='__main__': raise SystemExit(main())
