"""SQLite-backed audit trail for triage and human approval."""
import csv, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict
from engine import analyze, optional_llm_enhance

ROOT = Path(__file__).parent
DB = ROOT / "flowdesk.db"

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def initialize():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY, created_at TEXT, customer TEXT, plan TEXT,
        channel TEXT, text TEXT, affected_users INTEGER, gold_category TEXT, gold_priority TEXT, incident_group TEXT,
        status TEXT NOT NULL DEFAULT 'New');
        CREATE TABLE IF NOT EXISTS analyses (ticket_id TEXT PRIMARY KEY, data TEXT NOT NULL, reviewed_reply TEXT,
        FOREIGN KEY(ticket_id) REFERENCES tickets(id));
        CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id TEXT NOT NULL,
        at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL);
        ''')
        n=c.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if not n:
            with (ROOT/"data"/"tickets.csv").open(encoding="utf-8", newline="") as f:
                data=list(csv.DictReader(f))
            c.executemany('''INSERT INTO tickets(id,created_at,customer,plan,channel,text,affected_users,gold_category,gold_priority,incident_group)
                VALUES (:id,:created_at,:customer,:plan,:channel,:text,:affected_users,:gold_category,:gold_priority,:incident_group)''',data)

def tickets():
    with conn() as c: return [dict(r) for r in c.execute("SELECT * FROM tickets ORDER BY created_at DESC")]

def get_ticket(ticket_id):
    with conn() as c:
        r=c.execute("SELECT * FROM tickets WHERE id=?",(ticket_id,)).fetchone()
        return dict(r) if r else None

def get_analysis(ticket_id):
    with conn() as c:
        r=c.execute("SELECT * FROM analyses WHERE ticket_id=?",(ticket_id,)).fetchone()
        return (json.loads(r["data"]),r["reviewed_reply"]) if r else (None,None)

def event(c, ticket_id, actor, action, detail=""):
    c.execute("INSERT INTO events(ticket_id,at,actor,action,detail) VALUES (?,?,?,?,?)", (ticket_id, datetime.now(timezone.utc).isoformat(),actor,action,detail))

def run_triage(ticket_id):
    t=get_ticket(ticket_id)
    if not t: raise ValueError("Unknown ticket")
    result=optional_llm_enhance(t,analyze(t, tickets()))
    with conn() as c:
        c.execute("INSERT INTO analyses(ticket_id,data) VALUES (?,?) ON CONFLICT(ticket_id) DO UPDATE SET data=excluded.data, reviewed_reply=NULL", (ticket_id, json.dumps(asdict(result))))
        c.execute("UPDATE tickets SET status='Awaiting review' WHERE id=?", (ticket_id,))
        event(c,ticket_id,"AI agent","triaged",result.reasoning)
    return asdict(result)

def action(ticket_id, actor, kind, reply=""):
    if kind not in {"Approve", "Resolve", "Reopen", "Escalate"}: raise ValueError("Unsupported action")
    analysis,_=get_analysis(ticket_id)
    if not analysis: raise ValueError("Triage the ticket first")
    old=get_ticket(ticket_id)["status"]
    if kind=="Approve" and old not in {"Awaiting review", "Escalated"}: raise ValueError("Approval requires pending review")
    if kind=="Resolve" and old!="Approved": raise ValueError("Human approval required before resolution")
    if kind=="Reopen" and old!="Resolved": raise ValueError("Only resolved tickets may reopen")
    if kind=="Escalate" and old not in {"Awaiting review","Approved"}: raise ValueError("Escalation requires triaged ticket")
    new={"Approve":"Approved", "Resolve":"Resolved", "Reopen":"Awaiting review", "Escalate":"Escalated"}[kind]
    with conn() as c:
        c.execute("UPDATE tickets SET status=? WHERE id=?",(new,ticket_id))
        if kind=="Approve":c.execute("UPDATE analyses SET reviewed_reply=? WHERE ticket_id=?",(reply or analysis["proposed_reply"],ticket_id))
        event(c,ticket_id,actor,kind,f"{old} -> {new}")

def add_ticket(text, customer, plan, affected_users):
    with conn() as c:
        n=c.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        ticket_id=f"LIVE-{n+1:04d}"
        c.execute('''INSERT INTO tickets(id,created_at,customer,plan,channel,text,affected_users,gold_category,gold_priority,incident_group)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',(ticket_id,datetime.now(timezone.utc).isoformat(),customer,plan,"Portal",text,affected_users,"","",""))
        event(c,ticket_id,"Customer","created")
    return ticket_id

def events(ticket_id=None):
    with conn() as c:
        q="SELECT * FROM events" + (" WHERE ticket_id=?" if ticket_id else "")+" ORDER BY event_id DESC"
        return [dict(r) for r in c.execute(q,(ticket_id,) if ticket_id else ())]
