"""A classical baseline: TF-IDF word features + gradient-boosted trees, one model per question.

It needs a label for every question and must be retrained when a question changes, but it is local,
instant and free. Predictions are out-of-fold (5-fold), so every ticket is predicted by a model that has
never seen it.
"""
from __future__ import annotations

from metrics import TEAMS


def run_xgboost(items: list[dict]) -> list[dict]:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import StratifiedKFold
    from xgboost import XGBClassifier

    texts = [i["text"] for i in items]
    rows = [{"id": i["id"], "latency": 0.0, "cost": 0.0, "error": None} for i in items]
    for task in ("team", "urgent", "refund"):
        classes = TEAMS if task == "team" else [False, True]
        y = np.array([classes.index(i[task]) for i in items])
        oof = np.zeros((len(items), len(classes)))
        for train, test in StratifiedKFold(5, shuffle=True, random_state=14).split(texts, y):
            vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            model = XGBClassifier(n_estimators=120, max_depth=3, learning_rate=0.1, verbosity=0)
            model.fit(vec.fit_transform([texts[i] for i in train]), y[train])
            proba = model.predict_proba(vec.transform([texts[i] for i in test]))
            for col, cls in enumerate(model.classes_):
                oof[test, cls] = proba[:, col]
        for row, p in zip(rows, oof):
            row[task] = dict(zip(TEAMS, map(float, p))) if task == "team" else float(p[1])
    return rows
