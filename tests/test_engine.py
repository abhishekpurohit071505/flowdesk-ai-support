from datetime import datetime,timezone
from engine import analyze, duplicate_score

NOW=datetime.now(timezone.utc).isoformat()
def ticket(id,txt,affected=1):
    return {"id":id,"text":txt,"affected_users":affected,"created_at":NOW}

def test_cross_tenant_security():
    r=analyze(ticket("X1","I can see another company invoices and payment details"))
    assert r.category=="Security" and r.priority=="P1" and r.needs_human

def test_outage_p0():
    r=analyze(ticket("X2","Our entire team cannot log in; business operations completely stopped",120))
    assert r.priority=="P0"

def test_feature_p3():
    r=analyze(ticket("X3","I love using FlowDesk. It would be great to add dark mode"))
    assert r.category=="Feature Request" and r.priority=="P3"

def test_duplicate():
    a="Our entire team cannot login and cannot access orders since morning"
    b="Everyone in our team cannot login and access orders since morning"
    assert duplicate_score(a,b)>0.55

def test_no_password_solicitation():
    r=analyze(ticket("X4","My password reset email never arrived"))
    assert "send us your password" not in r.proposed_reply.lower()
