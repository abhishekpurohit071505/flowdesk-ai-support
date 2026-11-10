# Product requirements — FlowDesk AI Support Agent

## Target users
- **Support associate:** Reduce time spent sorting routine tickets; preserve decision context.
- **Support manager:** Track high-risk incidents, allocation and human review capacity.
- **Security lead:** Detect potentially exposed customer records with high recall.

## Problem / opportunity
Ticket queues contain mixed urgency and noisy descriptions. Manual prioritization can be inconsistent; repeated incidents create duplicate effort. The proposed solution offers explainable recommendations and a mandatory human checkpoint.

## MVP requirements and acceptance criteria
| ID | Story | Acceptance criteria |
|---|---|---|
| ST-01 | As a customer, submit a ticket | Text, organization, plan and affected-user count are persisted with unique ID |
| ST-02 | As an agent, get automatic category | Category and evidence-based explanation shown; labels never fed from benchmark |
| ST-03 | As an agent, assess priority | P0–P3 with displayed reason and SLA policy |
| ST-04 | As a security responder, detect unsafe disclosures | Cross-tenant data issues route to Security and require review |
| ST-05 | As a support agent, find duplicates | Suggested matches show score and do not merge automatically |
| ST-06 | As a support agent, propose reply | Draft is editable and not automatically sent |
| ST-07 | As a reviewer, approve or escalate | Only approved tickets can be marked resolved |
| ST-08 | As a manager, inspect workflow | Queue status, category and priority charts, events are visible |
| ST-09 | As a PM, measure performance | Benchmark labels and predictions can be compared, errors downloadable |

## Prioritization
**Must:** Intake, classification, severity, routing, review gating, audit events, synthetic test set.
**Should:** Duplicate suggestions, SLA flags, dashboard and benchmark.
**Could:** Grounded knowledge retrieval, sandbox integrations, human feedback learning.
**Won't (MVP):** Real customer messaging or automated operational account actions.

## Experiment design
Run a limited controlled pilot with non-sensitive synthetic or consented redacted data. Compare median handling time and classification/priority agreement against the same cases processed manually; have blinded reviewers adjudicate high-risk escalations. Do not infer impact from a synthetic offline benchmark alone.

## Key risks
- Missed critical incidents → conservative severity policy; review gate; evaluate high-risk recall.
- Sensitive data mishandling → synthetic data, redaction policy and no automatic outgoing messages.
- Hallucinated procedures → safe response templates for sensitive categories; later KB citations.
- Model drift → error analysis and human-labeled holdout set.
