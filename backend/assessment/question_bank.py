"""
assessment/question_bank.py — Module 11: Skill Assessment Engine (data).

All questions are structured as single-best-answer multiple choice so they
can be graded automatically in a browser-only demo with no code-execution
sandbox. The "type" field still reflects the cognitive style the brief
asks for (mcq / predict_output / debugging / coding / scenario) — a
"coding" question, for example, asks the learner to pick the correct
implementation rather than write and execute free code. This is a
deliberate, disclosed simplification (see README limitations), not an
attempt to claim a full code-judge exists.

Curated for the same 10 skills as learning/content.py so Learn -> Practice
-> Test forms one complete loop for a compelling demo across every roadmap
level. Other skills fall back to "not yet available" (assessment/engine.py)
rather than generating meaningless filler questions.
"""
from typing import Dict, List

# Each question: id, type, topic, prompt, options[4], correct_index, explanation
QUESTION_BANK: Dict[str, List[Dict]] = {
    "python": [
        {"id": "py1", "type": "mcq", "topic": "data_types", "prompt": "Which of these is immutable in Python?",
         "options": ["list", "dict", "tuple", "set"], "correct_index": 2,
         "explanation": "Tuples are immutable; lists, dicts, and sets can all be modified in place."},
        {"id": "py2", "type": "predict_output", "topic": "control_flow", "prompt": "What does this print?\n\nfor i in range(3):\n    print(i * 2)",
         "options": ["0 2 4", "1 2 3", "0 1 2", "2 4 6"], "correct_index": 0,
         "explanation": "range(3) yields 0,1,2; each is multiplied by 2 -> 0, 2, 4."},
        {"id": "py3", "type": "debugging", "topic": "functions", "prompt": "This function should return the sum of a list but throws an error on an empty list. What's the safest fix?\n\ndef total(nums):\n    return sum(nums) / len(nums)",
         "options": ["Remove the division entirely — the bug is using / instead of a loop", "Add `if not nums: return 0` before dividing", "Use nums[0] instead of sum(nums)", "Wrap it in a try/except that does nothing"],
         "correct_index": 1, "explanation": "Guarding the empty case avoids a ZeroDivisionError while keeping the intended average logic."},
        {"id": "py4", "type": "coding", "topic": "comprehensions", "prompt": "Which snippet correctly returns the squares of only the even numbers in `nums`?",
         "options": ["[n**2 for n in nums if n % 2 == 0]", "[n**2 for n in nums if n % 2 == 1]", "[n for n in nums if n**2 % 2 == 0]", "{n**2 for n in nums}"],
         "correct_index": 0, "explanation": "The filter `if n % 2 == 0` keeps even numbers before squaring them."},
        {"id": "py5", "type": "scenario", "topic": "best_practice", "prompt": "You're processing a 5M-row CSV in a plain Python for-loop and it's too slow. What's the most impactful first change?",
         "options": ["Rewrite in a faster language", "Switch to pandas/numpy vectorized operations", "Add more print statements to debug", "Increase the recursion limit"],
         "correct_index": 1, "explanation": "Vectorized pandas/numpy operations avoid the per-row Python interpreter overhead that makes plain loops slow at scale."},
    ],
    "git": [
        {"id": "git1", "type": "mcq", "topic": "basics", "prompt": "Which command creates a new branch AND switches to it in one step?",
         "options": ["git branch feature", "git checkout -b feature", "git merge feature", "git switch --list"], "correct_index": 1,
         "explanation": "`git checkout -b <name>` creates and switches to the branch in one command."},
        {"id": "git2", "type": "predict_output", "topic": "status", "prompt": "You edit a tracked file but don't stage it. What does `git status` show for that file?",
         "options": ["Nothing — it's ignored", "Changes to be committed", "Changes not staged for commit", "Untracked file"], "correct_index": 2,
         "explanation": "Modified-but-unstaged tracked files show under \"Changes not staged for commit\"."},
        {"id": "git3", "type": "debugging", "topic": "conflicts", "prompt": "A merge shows `<<<<<<<`, `=======`, `>>>>>>>` markers in a file. What must you do before committing?",
         "options": ["Delete the file and re-clone", "Manually resolve the conflict markers and remove them, then git add the file", "Run git push --force", "Ignore it — git resolves it automatically on commit"],
         "correct_index": 1, "explanation": "Conflict markers must be manually resolved and removed; then the file is staged and the merge committed."},
        {"id": "git4", "type": "coding", "topic": "workflow", "prompt": "Which sequence correctly commits a change and pushes it to a remote branch called `feature/login`?",
         "options": ["git commit -m 'msg' -> git add . -> git push", "git add . -> git commit -m 'msg' -> git push origin feature/login", "git push -> git add . -> git commit", "git clone -> git commit -> git push"],
         "correct_index": 1, "explanation": "Stage (add), then commit, then push — in that order."},
        {"id": "git5", "type": "scenario", "topic": "best_practice", "prompt": "You accidentally committed a large binary file. What's the best next step for a shared branch that's already been pushed?",
         "options": ["Delete the repo and start over", "Use git filter-repo / BFG to remove it from history, coordinate with the team, then force-push", "Just delete the file in a new commit", "Rename the file"],
         "correct_index": 1, "explanation": "Deleting the file in a new commit leaves it in history; history rewriting (with team coordination) is needed to actually remove it."},
    ],
    "sql": [
        {"id": "sql1", "type": "mcq", "topic": "clauses", "prompt": "Which clause filters rows BEFORE grouping happens?",
         "options": ["HAVING", "WHERE", "GROUP BY", "ORDER BY"], "correct_index": 1,
         "explanation": "WHERE filters individual rows before GROUP BY runs; HAVING filters after grouping/aggregation."},
        {"id": "sql2", "type": "predict_output", "topic": "joins", "prompt": "Table A has 3 rows, Table B has 0 matching rows for any of them. What does `SELECT * FROM A LEFT JOIN B ON A.id = B.a_id` return?",
         "options": ["0 rows", "3 rows, B columns all NULL", "Error", "3 rows, only from A"], "correct_index": 1,
         "explanation": "LEFT JOIN keeps every row from A even with no match, filling B's columns with NULL."},
        {"id": "sql3", "type": "debugging", "topic": "aggregation", "prompt": "This query errors: `SELECT department, name, AVG(salary) FROM employees GROUP BY department`. Why?",
         "options": ["AVG isn't a valid SQL function", "`name` isn't in GROUP BY and isn't aggregated", "GROUP BY must come before SELECT", "You can't SELECT more than 2 columns"],
         "correct_index": 1, "explanation": "Every selected non-aggregated column must appear in GROUP BY; `name` doesn't, which most SQL engines reject."},
        {"id": "sql4", "type": "coding", "topic": "aggregation", "prompt": "Which query correctly returns departments with more than 5 employees?",
         "options": ["SELECT department FROM employees WHERE COUNT(*) > 5", "SELECT department, COUNT(*) FROM employees GROUP BY department HAVING COUNT(*) > 5", "SELECT department FROM employees GROUP BY department WHERE COUNT(*) > 5", "SELECT COUNT(department) FROM employees"],
         "correct_index": 1, "explanation": "Filtering on an aggregate requires HAVING, applied after GROUP BY."},
        {"id": "sql5", "type": "scenario", "topic": "performance", "prompt": "A query filtering on `email` is slow on a 10M-row table. What's the most direct fix?",
         "options": ["Rewrite the query in a different language", "Add an index on the `email` column", "Remove the WHERE clause", "Switch to a NoSQL database"],
         "correct_index": 1, "explanation": "An index on the filtered column lets the database avoid a full table scan."},
    ],
    "statistics": [
        {"id": "st1", "type": "mcq", "topic": "central_tendency", "prompt": "Which measure is least affected by extreme outliers?",
         "options": ["Mean", "Median", "Range", "Standard deviation"], "correct_index": 1,
         "explanation": "The median depends only on rank order, so a few extreme values barely move it, unlike the mean."},
        {"id": "st2", "type": "predict_output", "topic": "distributions", "prompt": "A fair coin is flipped 4 times. What's the probability of getting exactly 2 heads?",
         "options": ["1/4", "3/8", "1/2", "1/16"], "correct_index": 1,
         "explanation": "C(4,2) * 0.5^4 = 6/16 = 3/8."},
        {"id": "st3", "type": "debugging", "topic": "hypothesis_testing", "prompt": "A report claims \"p=0.04, so there's a 96% chance the new design is better.\" What's wrong with this statement?",
         "options": ["Nothing, it's correct", "p-values don't give the probability a hypothesis is true — that's a common misinterpretation", "p should be compared to 0.5, not 0.05", "The sample size makes this invalid"],
         "correct_index": 1, "explanation": "A p-value is P(data this extreme | null hypothesis true), not the probability the alternative hypothesis is true."},
        {"id": "st4", "type": "coding", "topic": "computation", "prompt": "Which correctly computes the sample standard deviation of a list `x` in Python without numpy?",
         "options": ["sum(x) / len(x)", "(sum((v - sum(x)/len(x))**2 for v in x) / (len(x)-1)) ** 0.5", "max(x) - min(x)", "sum(x**2) / len(x)"],
         "correct_index": 1, "explanation": "Sample std dev = sqrt(sum of squared deviations from the mean / (n-1))."},
        {"id": "st5", "type": "scenario", "topic": "experiment_design", "prompt": "An A/B test shows the variant is better with p=0.15. What should you conclude?",
         "options": ["The variant is definitely better, ship it", "The result isn't statistically significant at the typical 0.05 threshold — don't conclude a real effect yet", "p=0.15 is always meaningless", "Run the test on fewer users to fix it"],
         "correct_index": 1, "explanation": "p=0.15 exceeds the common 0.05 significance threshold, so the observed difference could plausibly be noise."},
    ],
    "pandas": [
        {"id": "pd1", "type": "mcq", "topic": "basics", "prompt": "Which method returns the first 5 rows of a DataFrame `df`?",
         "options": ["df.top()", "df.head()", "df.first(5)", "df.sample()"], "correct_index": 1,
         "explanation": "`.head()` (default n=5) returns the first rows."},
        {"id": "pd2", "type": "predict_output", "topic": "filtering", "prompt": "df has a column 'age' with values [15, 22, 30]. What does `df[df.age > 20].shape[0]` return?",
         "options": ["1", "2", "3", "0"], "correct_index": 1,
         "explanation": "22 and 30 are both > 20, so 2 rows match."},
        {"id": "pd3", "type": "debugging", "topic": "copy_semantics", "prompt": "`df[df.age > 20]['score'] = 0` raises a SettingWithCopyWarning and doesn't reliably update df. What's the fix?",
         "options": ["Ignore the warning, it's harmless", "Use df.loc[df.age > 20, 'score'] = 0", "Use df.age > 20 twice", "Convert df to a list first"],
         "correct_index": 1, "explanation": "Chained indexing can operate on a copy; `.loc` with a boolean mask + column updates the original DataFrame reliably."},
        {"id": "pd4", "type": "coding", "topic": "groupby", "prompt": "Which correctly computes total revenue per region, sorted highest first?",
         "options": ["df.groupby('region').sum()", "df.groupby('region')['revenue'].sum().sort_values(ascending=False)", "df.sort_values('region')['revenue']", "df['revenue'].groupby().sum()"],
         "correct_index": 1, "explanation": "groupby('region')['revenue'].sum() aggregates revenue per region; sort_values(ascending=False) orders it highest-first."},
        {"id": "pd5", "type": "scenario", "topic": "missing_data", "prompt": "A column is 30% missing values (NaN). What's a reasonable first step before modeling?",
         "options": ["Always drop the column immediately", "Investigate why it's missing, then decide between imputation, a missing-indicator flag, or dropping based on that reason", "Replace all NaN with 0 without checking", "Ignore it — models handle NaN automatically"],
         "correct_index": 1, "explanation": "The right handling depends on *why* data is missing; blindly dropping or zero-filling can introduce bias."},
    ],
    "numpy": [
        {"id": "np1", "type": "mcq", "topic": "arrays", "prompt": "What is `np.array([1,2,3]).shape`?",
         "options": ["(3,)", "(1,3)", "(3,1)", "3"], "correct_index": 0,
         "explanation": "A 1D array of 3 elements has shape (3,)."},
        {"id": "np2", "type": "predict_output", "topic": "broadcasting", "prompt": "What does `np.array([1,2,3]) + np.array([10,20,30])` return?",
         "options": ["[11, 22, 33]", "Error — shapes don't match", "[1,2,3,10,20,30]", "60"], "correct_index": 0,
         "explanation": "Elementwise addition on equal-shaped arrays adds corresponding elements."},
        {"id": "np3", "type": "debugging", "topic": "broadcasting", "prompt": "`np.array([[1,2],[3,4]]) + np.array([1,2,3])` raises a broadcasting error. Why?",
         "options": ["NumPy can't add 2D and 1D arrays ever", "The trailing dimensions (2 vs 3) don't match and aren't broadcastable", "You must convert to a list first", "Addition requires the same dtype"],
         "correct_index": 1, "explanation": "Broadcasting requires trailing dimensions to match or be 1; 2 vs 3 is incompatible."},
        {"id": "np4", "type": "coding", "topic": "vectorization", "prompt": "Which is the vectorized (fast) way to compute elementwise squares of a large array `a`?",
         "options": ["[x**2 for x in a]", "a ** 2", "list(map(lambda x: x*x, a))", "for x in a: x = x**2"],
         "correct_index": 1, "explanation": "`a ** 2` applies the operation to the whole array in optimized C code, no Python-level loop."},
        {"id": "np5", "type": "scenario", "topic": "performance", "prompt": "You're looping over a NumPy array in pure Python to sum its elements, and it's slow on 10M elements. Best fix?",
         "options": ["Use a[i] indexing in a tighter loop", "Use a.sum() (vectorized reduction)", "Convert to a Python list first", "Use recursion instead of a loop"],
         "correct_index": 1, "explanation": "NumPy's built-in reductions (.sum(), .mean(), etc.) run in optimized C and avoid Python loop overhead entirely."},
    ],
    "machine_learning": [
        {"id": "ml1", "type": "mcq", "topic": "fundamentals", "prompt": "What is the main purpose of a train/test split?",
         "options": ["To make training faster", "To estimate how the model performs on unseen data", "To reduce the number of features", "To remove outliers"], "correct_index": 1,
         "explanation": "Held-out test data estimates generalization performance, since evaluating on training data is optimistic."},
        {"id": "ml2", "type": "predict_output", "topic": "overfitting", "prompt": "Training accuracy is 99%, test accuracy is 61%. What's most likely happening?",
         "options": ["Underfitting", "Overfitting", "Perfect fit", "A labeling bug in the test set only"], "correct_index": 1,
         "explanation": "A large gap between high training accuracy and much lower test accuracy is the classic signature of overfitting."},
        {"id": "ml3", "type": "debugging", "topic": "evaluation", "prompt": "A fraud model gets 99% accuracy but misses almost every actual fraud case (fraud is 1% of data). What's the real problem?",
         "options": ["Nothing — 99% is great", "Accuracy is misleading on this imbalanced dataset; precision/recall on the fraud class should be used instead", "The model needs more training epochs", "The dataset is too large"],
         "correct_index": 1, "explanation": "On heavily imbalanced data, always-predict-majority-class already gets high accuracy; precision/recall/F1 on the minority class reveal the real performance."},
        {"id": "ml4", "type": "coding", "topic": "workflow", "prompt": "Which snippet correctly evaluates a model without leaking test data into training?",
         "options": ["model.fit(X, y); model.score(X, y)", "X_train, X_test, y_train, y_test = train_test_split(X, y); model.fit(X_train, y_train); model.score(X_test, y_test)", "model.fit(X_test, y_test); model.score(X_train, y_train)", "model.score(X, y) before fitting"],
         "correct_index": 1, "explanation": "Fit only on the training split, evaluate only on the held-out test split."},
        {"id": "ml5", "type": "scenario", "topic": "model_selection", "prompt": "You have a small (500-row) labeled dataset and need an interpretable baseline fast. What's a reasonable first model to try?",
         "options": ["A 100-layer deep neural network", "Logistic regression or a small decision tree", "A large language model fine-tune", "Skip modeling and just report the mean"], "correct_index": 1,
         "explanation": "Simple, interpretable models are the right starting baseline on small data before reaching for complex, data-hungry approaches."},
    ],
    "deep_learning": [
        {"id": "dl1", "type": "mcq", "topic": "fundamentals", "prompt": "What does an activation function primarily introduce into a neural network?",
         "options": ["More parameters only", "Non-linearity", "Faster training automatically", "Regularization"], "correct_index": 1,
         "explanation": "Without non-linear activations, stacking linear layers would still collapse to one linear function."},
        {"id": "dl2", "type": "predict_output", "topic": "training", "prompt": "Training loss keeps dropping but validation loss starts rising after epoch 10. What's happening around epoch 10+?",
         "options": ["Underfitting begins", "The model starts overfitting to the training set", "The learning rate is too low", "The data loader is broken"], "correct_index": 1,
         "explanation": "Diverging train/val loss (train down, val up) is the textbook overfitting curve."},
        {"id": "dl3", "type": "debugging", "topic": "training", "prompt": "Loss is `NaN` after a few training steps. What's a common cause to check first?",
         "options": ["Too much data", "Learning rate too high, causing exploding gradients", "Too few epochs", "Using ReLU instead of sigmoid"], "correct_index": 1,
         "explanation": "A too-high learning rate is one of the most common causes of exploding gradients and NaN loss."},
        {"id": "dl4", "type": "coding", "topic": "architecture", "prompt": "For classifying 28x28 grayscale images into 10 classes, which output layer is correct?",
         "options": ["nn.Linear(784, 1)", "nn.Linear(128, 10)", "nn.Linear(10, 784)", "nn.Linear(28, 28)"], "correct_index": 1,
         "explanation": "The final layer should map hidden features to 10 output logits, one per class."},
        {"id": "dl5", "type": "scenario", "topic": "practical", "prompt": "You have only 500 labeled images and want good accuracy for image classification. What's usually the most effective approach?",
         "options": ["Train a huge CNN from scratch", "Use transfer learning from a pretrained model and fine-tune", "Skip deep learning entirely, it never works on small data", "Use a single-layer perceptron"], "correct_index": 1,
         "explanation": "Transfer learning from a model pretrained on large datasets is the standard, effective approach on small labeled datasets."},
    ],
    "nlp": [
        {"id": "nlp1", "type": "mcq", "topic": "preprocessing", "prompt": "What does tokenization do?",
         "options": ["Removes stopwords only", "Splits text into words/subwords/tokens for processing", "Translates text to another language", "Compresses text for storage"], "correct_index": 1,
         "explanation": "Tokenization breaks raw text into discrete units (tokens) a model can operate on."},
        {"id": "nlp2", "type": "predict_output", "topic": "tfidf", "prompt": "A word appears in every single document in a TF-IDF corpus. What happens to its IDF weight?",
         "options": ["It becomes very high", "It approaches zero, making the term less important", "It stays constant at 1", "TF-IDF ignores it entirely"], "correct_index": 1,
         "explanation": "IDF penalizes terms that appear in most/all documents since they carry little discriminating information."},
        {"id": "nlp3", "type": "debugging", "topic": "preprocessing", "prompt": "A sentiment classifier performs poorly because \"not good\" is being scored the same as \"good\". What's the likely cause?",
         "options": ["The model needs more data only", "Bag-of-words / unigram features lose word order, so negation context is lost", "The learning rate is too high", "The dataset is too large"], "correct_index": 1,
         "explanation": "Plain bag-of-words treats \"not\" and \"good\" independently, losing the negation relationship that bigrams or sequence models capture."},
        {"id": "nlp4", "type": "coding", "topic": "vectorization", "prompt": "Which correctly builds TF-IDF features for a list of documents `docs` using scikit-learn?",
         "options": ["CountVectorizer().fit(docs)", "TfidfVectorizer().fit_transform(docs)", "TfidfVectorizer().predict(docs)", "TfidfVectorizer(docs).transform()"], "correct_index": 1,
         "explanation": "`fit_transform` learns the vocabulary/IDF weights and returns the TF-IDF matrix in one call."},
        {"id": "nlp5", "type": "scenario", "topic": "modern_nlp", "prompt": "You need to find semantically similar support tickets, even when they use different wording. What approach fits best?",
         "options": ["Exact string matching", "Sentence embeddings + cosine similarity", "Regular expressions only", "Sorting alphabetically"], "correct_index": 1,
         "explanation": "Embeddings capture meaning beyond surface wording, so semantically similar text ends up close in vector space even with different words."},
    ],
    "fastapi": [
        {"id": "fa1", "type": "mcq", "topic": "basics", "prompt": "What does FastAPI use to validate request bodies?",
         "options": ["Regular expressions only", "Pydantic models", "Manual if/else checks", "JSON Schema written by hand"], "correct_index": 1,
         "explanation": "FastAPI uses Pydantic models to validate and parse request/response data automatically."},
        {"id": "fa2", "type": "predict_output", "topic": "routing", "prompt": "You define `@app.get('/items/{item_id}')` with `def read_item(item_id: int)`. What happens if a client requests `/items/abc`?",
         "options": ["item_id becomes the string 'abc'", "FastAPI returns a 422 validation error", "The server crashes", "It silently returns None"], "correct_index": 1,
         "explanation": "FastAPI validates path parameters against their type hint; a non-integer for an `int` param returns a 422 error automatically."},
        {"id": "fa3", "type": "debugging", "topic": "cors", "prompt": "A frontend on a different port gets a CORS error calling your FastAPI backend. What's the fix?",
         "options": ["Restart the browser", "Add CORSMiddleware with the frontend's origin allowed", "Switch to GET requests only", "Disable HTTPS"], "correct_index": 1,
         "explanation": "CORSMiddleware must explicitly allow the calling origin, or the browser blocks the cross-origin response."},
        {"id": "fa4", "type": "coding", "topic": "endpoints", "prompt": "Which correctly defines a POST endpoint accepting a JSON body validated against a Pydantic model `Item`?",
         "options": ["@app.post('/items')\\ndef create(item: Item): ...", "@app.get('/items')\\ndef create(item): ...", "@app.post('/items')\\ndef create(item: str): ...", "@app.route('/items')\\ndef create(item): ..."], "correct_index": 0,
         "explanation": "A POST route with a parameter typed as the Pydantic model automatically validates and parses the JSON body."},
        {"id": "fa5", "type": "scenario", "topic": "architecture", "prompt": "You need to serve a trained ML model's predictions to a web frontend. What's a reasonable minimal architecture?",
         "options": ["Email the frontend developer the model file", "A FastAPI endpoint that loads the model once at startup and exposes a POST /predict route", "Run the model inside the browser only", "Recompute the model on every git push"], "correct_index": 1,
         "explanation": "Loading the model once at startup and exposing a prediction endpoint is the standard lightweight ML-serving pattern."},
    ],
}


def has_assessment(skill_key: str) -> bool:
    return skill_key in QUESTION_BANK


def get_questions(skill_key: str) -> List[Dict]:
    return QUESTION_BANK.get(skill_key, [])


AVAILABLE_ASSESSMENT_SKILLS = sorted(QUESTION_BANK.keys())
