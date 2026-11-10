"""FlowDesk AI Support: Streamlit portfolio demo."""
import json, os
from pathlib import Path
import pandas as pd
import streamlit as st
from storage import initialize, tickets, get_ticket, get_analysis, run_triage, action, add_ticket, events
from evaluation import evaluate

st.set_page_config(page_title="FlowDesk | AI Support Operations", page_icon="🎫", layout="wide")
initialize()
st.title("🎫 FlowDesk — AI Support Operations")
st.caption("A product-management portfolio demo • synthetic tickets • explainable triage • human-in-the-loop")
if os.getenv("USE_LLM") == "1" and os.getenv("OPENAI_API_KEY"):
    st.success("OpenAI language enhancement enabled. Classification and guardrails remain rules-based.")
else:
    st.info("Demo mode: works without an API key. Optional OpenAI enhancement can refine safe, low-risk reply drafts.")

tab_inbox, tab_create, tab_insights, tab_benchmark, tab_audit, tab_about = st.tabs([
    "📥 Ticket inbox", "➕ Submit a ticket", "📊 Operations dashboard", "🧪 AI benchmark", "🕒 Audit trail", "📘 Product case study"])

with tab_inbox:
    data=tickets()
    cols=st.columns(4)
    for col,(label,val) in zip(cols,[("Total tickets",len(data)),("Untriaged",sum(x['status']=='New' for x in data)),
                                 ("Awaiting review",sum(x['status']=='Awaiting review' for x in data)),
                                 ("Resolved",sum(x['status']=='Resolved' for x in data))]):
        col.metric(label,val)
    status_filter=st.selectbox("Filter by status",["All","New","Awaiting review","Escalated","Approved","Resolved"])
    visible=[t for t in data if status_filter=="All" or t["status"]==status_filter]
    df=pd.DataFrame(visible)
    st.dataframe(df[["id","customer","plan","channel","affected_users","status","text"]].rename(columns={"id":"Ticket ID", "text":"Customer issue"}), use_container_width=True, hide_index=True, height=245)
    if visible:
        selected=st.selectbox("Open ticket",[x['id'] for x in visible],format_func=lambda i: f"{i} — {next(x['text'][:75] for x in visible if x['id']==i)}")
        t=get_ticket(selected)
        analysis,approved_reply=get_analysis(selected)
        left,right=st.columns([1,1.25],gap="large")
        with left:
            st.subheader("Customer submission")
            st.write(t["text"])
            st.caption(f"{t['customer']} · {t['plan']} · {t['affected_users']} user(s) affected · {t['created_at']}")
            if st.button("🧠 Run AI triage", type="primary", key=f"triage_{selected}"):
                run_triage(selected); st.rerun()
            if analysis:
                st.markdown("**Ticket lifecycle**")
                st.write(f"Current status: **{t['status']}**")
                if analysis["duplicate_of"]:
                    st.warning(f"Possible duplicate of **{analysis['duplicate_of']}** (score {analysis['similarity']:.2f}); human confirmation required")
                st.caption("Duplicate matching is heuristic; similarity is not a calibrated probability.")
        with right:
            st.subheader("AI decision and review")
            if not analysis:
                st.info("Run AI triage to see classification, risk assessment, and drafted response.")
            else:
                c1,c2,c3=st.columns(3)
                c1.metric("Priority",analysis["priority"])
                c2.metric("Category",analysis["category"])
                c3.metric("Sentiment",analysis["sentiment"])
                st.write(f"**Route to:** {analysis['team']}")
                st.write(f"**SLA:** {analysis['sla_status']} · first response due {analysis['sla_due_at']}")
                st.write(f"**Explanation:** {analysis['reasoning']}")
                st.write(f"**Confidence heuristic:** {analysis['confidence']:.0%} (not a statistically calibrated probability)")
                st.write("**Suggested next actions:**")
                for a in analysis["next_actions"]:st.write("• " + a)
                st.warning("Human approval required" if analysis["needs_human"] else "Agent-assisted draft; human approval required before closing")
                draft=st.text_area("Review and edit proposed reply",value=approved_reply or analysis["proposed_reply"],height=205,key=f"reply_{selected}")
                st.caption("Draft-only workflow: this demo does not send messages or issue refunds.")
                if t['status'] in {'Awaiting review','Escalated'}:
                    x,y=st.columns(2)
                    if x.button("✅ Approve draft", key=f"approve_{selected}"):
                        action(selected,"Demo reviewer","Approve",draft);st.rerun()
                    if y.button("🚨 Escalate", key=f"escalate_{selected}"):
                        action(selected,"Demo reviewer","Escalate");st.rerun()
                if t['status']=='Approved':
                    st.success("Draft approved for external handling (not actually sent).")
                    if st.button("✓ Mark as resolved",key=f"resolve_{selected}"):
                        action(selected,"Demo reviewer","Resolve");st.rerun()
                if t['status']=='Resolved' and st.button("↩ Reopen ticket",key=f"reopen_{selected}"):
                    action(selected,"Demo reviewer","Reopen");st.rerun()
                with st.expander("Raw structured AI output"):
                    st.json(analysis)

with tab_create:
    st.subheader("Simulate a new customer ticket")
    with st.form("new_ticket",clear_on_submit=True):
        customer=st.text_input("Customer / organization",value="Acme Demo Ltd")
        plan=st.selectbox("Plan",["Starter","Business","Enterprise"])
        affected=st.number_input("Affected users",1,100000,1)
        body=st.text_area("Customer message",placeholder="E.g. An invoice from another company is visible to our users...",height=145)
        submit=st.form_submit_button("Create ticket",type="primary")
    if submit:
        if len(body.strip())<12:st.error("Enter at least 12 characters.")
        else:
            new_id=add_ticket(body.strip(),customer.strip() or "Demo customer",plan,affected)
            st.success(f"Created {new_id}. Open the Ticket inbox and run triage.")

with tab_insights:
    st.subheader("Operations and workflow metrics")
    data=tickets()
    analyses=[(x,get_analysis(x['id'])[0]) for x in data]
    analyzed=[(x,a) for x,a in analyses if a]
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Tickets triaged",len(analyzed))
    m2.metric("Human reviewed",sum(x['status'] in {'Approved','Resolved'} for x in data))
    m3.metric("Escalated",sum(x['status']=='Escalated' for x in data))
    m4.metric("Flagged SLA breach",sum(a['sla_status']=='Breached' for _,a in analyzed))
    if analyzed:
        breakdown=pd.DataFrame([{**{'id':t['id'],'status':t['status']},**{k:a[k] for k in ['category','priority','team','sla_status','needs_human']}} for t,a in analyzed])
        a,b=st.columns(2)
        with a:
            st.markdown("**Ticket categories**");st.bar_chart(breakdown['category'].value_counts())
            st.markdown("**Workflow status**");st.bar_chart(pd.Series([t['status'] for t in data]).value_counts())
        with b:
            st.markdown("**Priority mix**");st.bar_chart(breakdown['priority'].value_counts())
            st.markdown("**Assigned teams**");st.bar_chart(breakdown['team'].value_counts())
        st.dataframe(breakdown,use_container_width=True,hide_index=True)
        st.download_button("Download analyzed tickets (CSV)",breakdown.to_csv(index=False).encode('utf-8'),"flowdesk-operations.csv","text/csv")
    else:st.info("Triage some tickets in the inbox to populate this dashboard.")
    st.caption("Operational metrics reflect this local SQLite demo. SLA calculations use synthetic ticket timestamps and a sample policy; no real response delivery is measured.")

with tab_benchmark:
    st.subheader("Offline benchmark (gold labels held out from inference)")
    results=evaluate()
    a,b,c=st.columns(3)
    a.metric("Tickets evaluated",results['n'])
    b.metric("Category accuracy",f"{results['category_accuracy']}%")
    c.metric("Priority accuracy",f"{results['priority_accuracy']}%")
    st.caption("Measured against a synthetic, author-labeled benchmark. Not an estimate of production accuracy, and not a claim of generalization. Priorities are provisional in some scenarios.")
    failures=pd.DataFrame(results['rows'])
    st.markdown("**Classification errors (use these to improve the product)**")
    st.dataframe(failures.loc[~failures.category_correct | ~failures.priority_correct],use_container_width=True,hide_index=True)
    st.download_button("Download benchmark results", failures.to_csv(index=False).encode('utf-8'),"flowdesk-benchmark.csv","text/csv")
    st.markdown("**Suggested next experiment**")
    st.write("Compare this rules-based baseline with an LLM classifier on a separate human-reviewed test set; measure macro-F1, P0/P1 escalation recall, duplicate precision, cost per ticket and human reviewer correction rate.")

with tab_audit:
    st.subheader("Immutable-style event history (append-only application log)")
    history=events()
    if history: st.dataframe(pd.DataFrame(history),use_container_width=True,hide_index=True)
    else:st.info("Create, triage or review tickets to generate audit events.")
    st.caption("Application-level append-only records; not a tamper-proof compliance audit system.")

with tab_about:
    st.subheader("Product case study")
    st.markdown('''
**Problem:** Manual support triage is inconsistent, slow, and prone to missed escalation signals.

**Users:** Tier-1 support agents, support operations managers, security responders, product managers.

**Hypothesis:** An explainable AI triage assistant with mandatory human review will reduce handling time while maintaining safe escalation.

**MVP scope:** Ticket intake → classification → impact/priority → routing → duplicate suggestion → SLA signals → reply draft → human approval → resolution → dashboard and audit events.

**Non-goals:** Automatically emailing customers, issuing refunds, modifying production accounts, or performing irreversible actions.

**Primary outcome metric:** Median time from ticket creation to first human-approved response (to be measured in a real pilot).

**Guardrail metrics:** Recall on security/high-severity incidents, erroneous auto-actions (target zero), reviewer correction rate, quality of customer replies.

**Suggested acceptance criteria:**
- Cross-tenant data exposure must route to Security and require human review.
- Critical multi-user outage should be prioritized as P0.
- No ticket can move to Resolved without review approval.
- Duplicate recommendations are non-destructive and reviewable.
- Every action is linked to a timestamped event.

**Roadmap:** Integrate Zendesk/Jira Service Management sandbox, add retrieved knowledge-base citations, model evaluations, queue-based SLA policies, reviewer feedback and auth/role control.
    ''')
    st.caption("This is a local portfolio prototype, not a production-ready support platform.")
