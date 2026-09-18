import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


# ---------------------------------------------
# 1) RULE-BASED CLASSIFIER (Heuristic)
# ---------------------------------------------
RULES = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "dominos", "pizza",
             "mcdonald", "kfc", "hotel", "dhaba", "bakery", "food"],
    "Transport": ["uber", "ola", "rapido", "petrol", "fuel", "diesel",
                  "irctc", "railway", "metro", "bus", "cab", "taxi", "toll"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa",
                 "reliance", "dmart", "bigbasket", "grocery", "mall"],
    "Utilities": ["electricity", "water", "gas", "broadband", "airtel",
                  "jio", "vodafone", "vi ", "bsnl", "recharge", "bill",
                  "municipal", "dth", "tata sky"],
    "Salary": ["salary", "payroll", "stipend", "wages", "neft cr"],
    "Transfer": ["upi", "imps", "neft", "rtgs", "transfer"],
    "ATM": ["atm", "cash withdrawal", "cash wdl", "nfs"],
    "Bills & EMI": ["insurance", "emi", "loan", "premium", "policy"],
    "Healthcare": ["hospital", "pharmacy", "medplus", "apollo", "clinic",
                   "medical", "doctor", "netmeds"],
    "Entertainment": ["netflix", "prime", "hotstar", "spotify", "bookmyshow",
                      "pvr", "inox", "youtube", "subscription"],
}


def rule_classify(description):
    """
    Classifies a transaction description using keyword rules.
    Returns a category string, or None if nothing matched.
    """
    d = description.lower()
    for category, keywords in RULES.items():
        if any(kw in d for kw in keywords):
            return category
    return None


# ---------------------------------------------
# 2) ML-BASED CLASSIFIER (TF-IDF + Logistic Regression)
# ---------------------------------------------
TRAIN_DATA = [
    ("swiggy order", "Food"),
    ("zomato lunch", "Food"),
    ("restaurant dinner", "Food"),
    ("dominos pizza", "Food"),
    ("cafe coffee day", "Food"),
    ("uber ride", "Transport"),
    ("ola cab booking", "Transport"),
    ("rapido bike", "Transport"),
    ("petrol pump", "Transport"),
    ("irctc ticket", "Transport"),
    ("amazon purchase", "Shopping"),
    ("flipkart order", "Shopping"),
    ("myntra clothes", "Shopping"),
    ("ajio fashion", "Shopping"),
    ("dmart grocery", "Shopping"),
    ("electricity bill", "Utilities"),
    ("jio recharge", "Utilities"),
    ("airtel postpaid", "Utilities"),
    ("broadband payment", "Utilities"),
    ("water bill", "Utilities"),
    ("salary credited", "Salary"),
    ("monthly salary", "Salary"),
    ("payroll transfer", "Salary"),
    ("upi transfer", "Transfer"),
    ("imps to friend", "Transfer"),
    ("neft to self", "Transfer"),
    ("atm withdrawal", "ATM"),
    ("cash wdl atm", "ATM"),
    ("nfs cash", "ATM"),
    ("emi payment", "Bills & EMI"),
    ("insurance premium", "Bills & EMI"),
    ("loan installment", "Bills & EMI"),
    ("apollo pharmacy", "Healthcare"),
    ("hospital bill", "Healthcare"),
    ("medplus order", "Healthcare"),
    ("netflix subscription", "Entertainment"),
    ("prime video", "Entertainment"),
    ("bookmyshow ticket", "Entertainment"),
    ("spotify premium", "Entertainment"),
]


def train_ml_classifier():
    """
    Trains a TF-IDF + Logistic Regression pipeline on the labeled samples.
    Returns a fitted sklearn Pipeline.
    """
    X = [d for d, _ in TRAIN_DATA]
    y = [c for _, c in TRAIN_DATA]

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    model.fit(X, y)
    return model


# ---------------------------------------------
# 3) HYBRID CLASSIFIER (Rules first, ML fallback)
# ---------------------------------------------
def classify_transactions(transactions, ml_model):
    """
    Assigns a category to each transaction.
    Tries rules first (fast, zero latency).
    Falls back to ML if no rule matches.
    """
    for txn in transactions:
        desc = txn.get("description", "") or ""
        category = rule_classify(desc)
        if category is None:
            try:
                category = ml_model.predict([desc])[0]
            except Exception:
                category = "Uncategorized"
        txn["category"] = category
    return transactions