"""Reproducible synthetic dataset, including edge cases and repeated incidents."""
import csv, random
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = [
("Authentication", "Our entire team is unable to log in since 9:15 AM. We have 120 employees using the platform and nobody can process customer orders. Business operations are completely stopped.","P0",120,"incident-login"),
("Billing", "I upgraded my account for ₹4,999, but my card was charged twice. Transaction IDs TXN7812 and TXN7813. I need a refund urgently.","P1",1,""),
("Security", "I logged in and noticed invoices belonging to another company. I can see their customer names, payment details, and invoice history. Is this supposed to happen?", "P1",1,""),
("Feature Request", "I love using FlowDesk. It would be great if you could add dark mode and customize dashboard colors.","P3",1,""),
("Reporting", "My dashboard isn't working properly. Numbers look strange and yesterday's reports don't match today's. I have a meeting in two hours.","P2",1,""),
("Authentication", "Everyone in our sales team is getting a login error since around 9:20 AM. We cannot access orders. Is there a system outage?", "P0",60,"incident-login"),
("Reporting", "This is the fourth time contacting support. Our invoice export has failed for three days and our compliance submission is tomorrow. Nobody has provided a solution.","P1",10,""),
("Account Settings", "How do I change my registered email address? I checked settings but could not find the option.","P3",1,""),
]
VARIANTS = {
"Authentication": ["Login page keeps refreshing with error 403 when I try to sign in.", "Our sales team cannot log in to their accounts after the last update.", "Password reset email never arrived. Please advise.", "The OTP code is rejected every time I sign in.", "I am locked out of my account after enabling 2FA."],
"Billing": ["My subscription renewal was charged twice on the same card.", "I need a corrected billing invoice for last month.", "The payment failed but my bank shows the transaction as complete.", "We were overcharged for extra seats on our plan.", "Can I change the payment method for my subscription?"],
"Security": ["I noticed a suspicious login from a device I do not recognize.", "Another company is visible in our customer dashboard and their data is exposed.", "Our team received a phishing email pretending to be FlowDesk support.", "I think an unauthorized user accessed our billing details.", "A shared account token appeared in a public log file."],
"Feature Request": ["Please add a dark mode for our dashboard.", "It would be great to have custom reports by region.", "Feature request: allow bulk editing of orders.", "Could you add keyboard shortcuts for ticket search?", "I wish you supported a configurable approval workflow."],
"Reporting": ["The revenue chart does not match the CSV export.", "My analytics report stopped updating yesterday.", "The dashboard shows an incorrect total for last week's sales.", "Export to CSV fails on the monthly report.", "My filtered report displays the wrong date range."],
"Integrations": ["Salesforce integration is not syncing new contacts.", "Our webhook endpoint receives duplicate order events.", "The API returns 429 errors during our nightly sync.", "The Zapier integration stopped after we rotated credentials.", "The integration token is rejected despite being renewed."],
"Orders": ["I cannot submit a new order from the checkout screen.", "Order status is stuck in processing for one customer.", "The inventory count is not decreasing after dispatch.", "Two shipments were created for the same purchase.", "A customer order has an incorrect shipping address."],
"Account Settings": ["How can I update my profile name?", "I want to change my registered email address.", "Where can I modify team member permissions?", "How do I remove a former employee from our workspace?", "Can our admin update the company address in settings?"],
"Performance": ["The app is very slow when opening the order list.", "The dashboard freezes after loading for a minute.", "We are seeing intermittent timeout errors in the browser.", "The order screen crashes when adding several line items.", "Search latency has increased this morning."],
}

def create_dataset(path: Path, count=100):
    rng = random.Random(42)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rows=[]
    for i in range(count):
        if i < len(BASE):
            category, text, priority, affected, incident = BASE[i]
        else:
            category = list(VARIANTS)[(i-len(BASE)) % len(VARIANTS)]
            text = VARIANTS[category][((i-len(BASE)) // len(VARIANTS)) % 5]
            prefix = ["Hi, ", "Hello team, ", "Need help: ", "", "Please investigate: "][i%5]
            suffix = ["", " This started today.", " Can someone help?", " Please advise."][i%4]
            text = prefix + text + suffix
            affected = 1 if category not in {"Authentication", "Performance", "Orders"} else [1,3,12][i%3]
            priority = "P1" if category == "Security" else "P3" if category in {"Feature Request", "Account Settings"} else "P2"
            incident = ""
        timestamp = now - timedelta(minutes=7*(i+1))
        rows.append({"id": f"TKT-{i+1:03d}", "created_at": timestamp.isoformat(), "customer": f"Demo Customer {((i*7)%31)+1:02d}",
            "plan": ["Starter", "Business", "Enterprise"][i%3], "channel": ["Email", "Chat", "Portal"][i%3],
            "text": text, "affected_users": affected, "gold_category": category, "gold_priority": priority, "incident_group": incident})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    return rows

if __name__=="__main__":
    p=Path(__file__).parent/"data"/"tickets.csv"
    create_dataset(p)
    print(p)
