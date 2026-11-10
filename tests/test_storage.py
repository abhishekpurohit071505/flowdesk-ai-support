import pytest
from storage import initialize, get_ticket, run_triage, action, get_analysis

def test_approval_gate(tmp_path,monkeypatch):
    import storage
    monkeypatch.setattr(storage,"DB",tmp_path/"test.db")
    initialize()
    with pytest.raises(ValueError):
        action("TKT-001","Reviewer","Resolve")
    triage=run_triage("TKT-001")
    assert triage['priority']=='P0'
    with pytest.raises(ValueError):
        action("TKT-001","Reviewer","Resolve")
    action("TKT-001","Reviewer","Approve", "Verified response")
    assert get_analysis("TKT-001")[1]=="Verified response"
    action("TKT-001","Reviewer","Resolve")
    assert get_ticket("TKT-001")['status']=="Resolved"
