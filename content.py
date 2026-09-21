"""
learning/content.py — Module 10: Learn stage of the Learning/Training System.

Hand-curated "Learn" content for the 10 skills that anchor a typical
Scratch -> Diamond path (spanning every level so the demo can show the
full journey). Every other skill in the 72-skill catalog still returns a
usable module built from real data already in skills_database.json
(course + project_ideas), clearly labeled as a lighter-weight guide rather
than pretending to have the same curated depth — see AVAILABLE_FULL below,
returned by the API so the frontend can be honest about which skills have
rich content.
"""
from typing import Dict, Optional

CURATED: Dict[str, Dict] = {
    "python": {
        "concept": "Python is a general-purpose, interpreted language and the backbone of almost every other skill in this roadmap — data, ML, and backend work all sit on top of it.",
        "key_topics": ["Variables & data types", "Control flow (if/for/while)", "Functions & scope", "Lists, dicts, sets, tuples", "Reading/writing files", "Exceptions (try/except)"],
        "example": "def average(nums):\n    return sum(nums) / len(nums) if nums else 0\n\nprint(average([4, 8, 15, 16, 23]))  # 13.2",
        "exercise": "Write a function that takes a list of resume skill strings and returns only the ones longer than 3 characters, with duplicates removed.",
        "key_points": ["Indentation defines blocks — there are no braces", "Everything is an object", "Prefer list/dict comprehensions once comfortable with loops"],
    },
    "git": {
        "concept": "Git tracks changes to your code over time and is how every project in this roadmap should be versioned — it's assumed knowledge for almost every job role.",
        "key_topics": ["init / clone", "add / commit", "branch / checkout", "merge & conflicts", "push / pull", ".gitignore"],
        "example": "git checkout -b feature/login\ngit add app.py\ngit commit -m \"Add login route\"\ngit push origin feature/login",
        "exercise": "Initialize a git repo for one of your existing scripts, make 3 commits with meaningful messages, then create and merge a branch.",
        "key_points": ["Commit early and often with clear messages", "Branches are cheap — use them for every feature", "A clean commit history is itself a portfolio signal"],
    },
    "sql": {
        "concept": "SQL is how you query and shape relational data — required for almost every data-adjacent role, independent of which ML framework you use.",
        "key_topics": ["SELECT / WHERE / ORDER BY", "GROUP BY & aggregates", "JOINs (inner/left)", "Subqueries", "Indexes (why queries are slow)"],
        "example": "SELECT department, AVG(salary)\nFROM employees\nGROUP BY department\nHAVING AVG(salary) > 60000;",
        "exercise": "Given an `orders` and `customers` table, write a query returning each customer's total spend, sorted highest first.",
        "key_points": ["JOIN before you filter with WHERE when possible, for clarity", "GROUP BY needs every non-aggregated selected column", "Explain plans reveal why a query is slow"],
    },
    "statistics": {
        "concept": "Statistics is the mathematical foundation under every ML metric and A/B test — without it, model evaluation numbers are just numbers.",
        "key_topics": ["Mean/median/variance/std dev", "Probability distributions", "Hypothesis testing & p-values", "Correlation vs causation", "Confidence intervals"],
        "example": "A/B test: control conversion 4.1%, variant 4.8%, p=0.03 -> statistically significant at the 5% level; report the effect size, not just the p-value.",
        "exercise": "Given two lists of conversion outcomes (0/1) for control and variant groups, compute the conversion rate difference and reason about whether it's likely to be noise.",
        "key_points": ["Correlation does not imply causation", "A p-value is not the probability the null hypothesis is true", "Always report effect size alongside significance"],
    },
    "pandas": {
        "concept": "pandas is the standard Python library for loading, cleaning, and reshaping tabular data before it goes anywhere near a model.",
        "key_topics": ["DataFrame / Series", "Filtering & indexing (.loc/.iloc)", "groupby & aggregation", "Merging/joining frames", "Handling missing data (NaN)"],
        "example": "import pandas as pd\ndf = pd.read_csv('sales.csv')\ntop = df.groupby('region')['revenue'].sum().sort_values(ascending=False)\nprint(top.head())",
        "exercise": "Load a CSV of transactions, drop rows with missing amounts, and compute monthly revenue totals.",
        "key_points": ["Vectorized operations beat Python loops", "Watch for SettingWithCopyWarning — it usually means a real bug", "groupby + agg covers most reporting needs"],
    },
    "numpy": {
        "concept": "NumPy provides fast array operations that pandas, scikit-learn, and most ML frameworks are built on top of — understanding arrays and broadcasting pays off everywhere.",
        "key_topics": ["ndarray basics", "Broadcasting", "Vectorized math vs loops", "Indexing & slicing", "Random number generation"],
        "example": "import numpy as np\na = np.array([1, 2, 3])\nb = np.array([10, 20, 30])\nprint(a * b)  # [10 40 90] — elementwise, no loop needed",
        "exercise": "Given a 2D array of exam scores (students x subjects), compute each student's average without writing a Python for-loop.",
        "key_points": ["Broadcasting avoids explicit loops for elementwise ops", "Arrays are fixed-type — mixed types get upcast", "Prefer numpy ops over pure-python math on large arrays"],
    },
    "machine_learning": {
        "concept": "Machine learning is about fitting a model to data so it generalizes to new, unseen examples — the core loop is train / evaluate / iterate, always on held-out data.",
        "key_topics": ["Train/test split", "Overfitting vs underfitting", "Supervised vs unsupervised", "Evaluation metrics (accuracy, precision/recall, RMSE)", "Cross-validation", "Feature engineering basics"],
        "example": "from sklearn.model_selection import train_test_split\nfrom sklearn.linear_model import LogisticRegression\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)\nmodel = LogisticRegression().fit(X_train, y_train)\nprint(model.score(X_test, y_test))",
        "exercise": "Train a classifier on a small labeled dataset and report accuracy AND a confusion matrix — accuracy alone can be misleading on imbalanced data.",
        "key_points": ["Never evaluate on data the model trained on", "Accuracy is misleading on imbalanced classes", "A simple baseline model is a mandatory sanity check"],
    },
    "deep_learning": {
        "concept": "Deep learning uses layered neural networks to learn representations directly from raw-ish data (pixels, text, audio) instead of hand-engineered features.",
        "key_topics": ["Neurons, layers, activations", "Forward pass & backpropagation", "Loss functions & optimizers", "Overfitting: dropout, regularization", "CNNs vs sequence models"],
        "example": "import torch.nn as nn\nmodel = nn.Sequential(nn.Linear(784, 128), nn.ReLU(), nn.Linear(128, 10))\n# forward pass: logits = model(x)",
        "exercise": "Train a small feed-forward network on a toy image dataset (e.g. MNIST-like) and plot train vs validation loss to spot overfitting.",
        "key_points": ["More layers ≠ automatically better — watch validation loss", "Learning rate is usually the single most important hyperparameter", "GPU isn't mandatory to learn the concepts on small datasets"],
    },
    "nlp": {
        "concept": "NLP is about turning text into something a model can reason over — from classic bag-of-words to modern transformer embeddings.",
        "key_topics": ["Tokenization", "Stopwords & normalization", "TF-IDF & bag-of-words", "Word/sentence embeddings", "Sequence models & transformers (high level)"],
        "example": "from sklearn.feature_extraction.text import TfidfVectorizer\nvec = TfidfVectorizer()\nX = vec.fit_transform([\"machine learning is fun\", \"deep learning is a subset of machine learning\"])\nprint(X.shape)",
        "exercise": "Build a simple spam/ham classifier using TF-IDF features and a logistic regression model.",
        "key_points": ["Tokenization choices change everything downstream", "TF-IDF is still a strong, fast baseline", "Embeddings capture meaning better than raw counts"],
    },
    "fastapi": {
        "concept": "FastAPI is a modern Python web framework for building the APIs that serve ML models and other backend logic — used to build this very project's backend.",
        "key_topics": ["Path & query parameters", "Pydantic request/response models", "Async endpoints", "Dependency injection", "Automatic OpenAPI docs"],
        "example": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'status': 'ok'}",
        "exercise": "Wrap a trained scikit-learn model behind a POST /predict endpoint that accepts JSON features and returns a prediction.",
        "key_points": ["Pydantic models give you free request validation", "/docs gives you an interactive API explorer for free", "Async endpoints matter most when calling other I/O, not CPU-bound ML inference"],
    },
}


def get_learning_module(skill_key: str, skills_db: dict) -> Optional[Dict]:
    meta = skills_db["skills"].get(skill_key)
    if not meta:
        return None
    label = meta["label"]

    if skill_key in CURATED:
        c = CURATED[skill_key]
        mini_project = skills_db["project_ideas"].get(skill_key, c["exercise"])
        return {
            "skill": skill_key, "label": label, "depth": "full",
            "concept": c["concept"], "key_topics": c["key_topics"],
            "example": c["example"], "exercise": c["exercise"],
            "mini_project": mini_project, "key_points": c["key_points"],
        }

    # Template fallback grounded in real DB fields — no fabricated depth claimed.
    courses = skills_db["courses"].get(skill_key, [])
    project = skills_db["project_ideas"].get(skill_key, "")
    return {
        "skill": skill_key, "label": label, "depth": "guide",
        "concept": f"{label} is part of the {meta['category']} category in this roadmap. A rich, curated lesson isn't built for this skill yet in this demo — start with the resource below.",
        "key_topics": [],
        "example": None,
        "exercise": project or f"Find a small, well-scoped way to apply {label} and build something with it.",
        "mini_project": project or f"Build something small using {label}.",
        "key_points": [f"Recommended starting resource: {courses[0]['name']} ({courses[0]['platform']})"] if courses else [],
    }


AVAILABLE_FULL_CONTENT_SKILLS = sorted(CURATED.keys())
