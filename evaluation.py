"""Offline benchmark. Ground truth is only used here, never during inference."""
import csv
from pathlib import Path
from engine import analyze, duplicate_score
ROOT=Path(__file__).parent

def evaluate():
    with (ROOT/"data"/"tickets.csv").open(encoding="utf-8", newline="") as f:
        rows=list(csv.DictReader(f))
    preds=[]
    for row in rows:
        result=analyze(row,[]) # evaluate independent classification (duplicate linkage evaluated separately)
        preds.append({"id":row["id"], "gold_category":row["gold_category"],"pred_category":result.category,
                      "gold_priority":row["gold_priority"],"pred_priority":result.priority,
                      "category_correct":row["gold_category"]==result.category,"priority_correct":row["gold_priority"]==result.priority})
    def accuracy(key):return round(100*sum(p[key] for p in preds)/len(preds),1)
    return {"category_accuracy":accuracy("category_correct"),"priority_accuracy":accuracy("priority_correct"),"n":len(rows),"rows":preds}
