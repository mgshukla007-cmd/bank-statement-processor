import sys
import os

# Allow importing from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.parser import extract_account_info, parse_transactions
from src.classifier import rule_classify, train_ml_classifier, classify_transactions


# ---------- Parser tests ----------

def test_extract_account_info():
    text = (
        "Account Holder: Rahul Sharma\n"
        "Account Number: 1234567890\n"
        "IFSC: HDFC0001234\n"
    )
    info = extract_account_info(text)
    assert info["account_holder"] == "Rahul Sharma"
    assert info["account_number"] == "1234567890"
    assert info["ifsc"] == "HDFC0001234"


def test_extract_account_info_bare_name_with_address():
    """Matches real HDFC / SC style: name on its own line, address below."""
    text = (
        "MR. BINAY KUMAR SHAW\n"
        "12/1A/35 CHOWBAGA ROAD KASBA\n"
        "KOLKATA 700039\n"
        "WEST BENGAL INDIA\n"
        "Account No. : 07181400100031\n"
        "IFSC: HDFC0000178\n"
    )
    info = extract_account_info(text)
    assert info["account_holder"] is not None
    assert "BINAY" in info["account_holder"].upper()
    assert info["account_number"] == "07181400100031"
    assert info["ifsc"] == "HDFC0000178"


def test_extract_account_info_account_name_label():
    """Matches UK-style 'Account name:' label."""
    text = (
        "Mr John Smith 5 Any Road Randomford\n"
        "Account name: Mr John Smith\n"
        "Account Type: Checking\n"
        "Account number: 99988877\n"
    )
    info = extract_account_info(text)
    assert info["account_holder"] == "Mr John Smith"
    assert info["account_number"] == "99988877"


def test_parse_debit_and_credit_by_balance_delta():
    text = (
        "15/01/2024 SWIGGY ORDER 450.00 12340.50\n"
        "16/01/2024 SALARY CREDITED 50000.00 62340.50\n"
    )
    txns = parse_transactions(text)
    assert len(txns) == 2
    assert txns[0]["debit"] == 450.00
    assert txns[0]["credit"] is None
    assert txns[1]["credit"] == 50000.00
    assert txns[1]["debit"] is None


def test_empty_text_returns_no_transactions():
    assert parse_transactions("") == []


def test_line_without_date_is_skipped():
    text = "This is a header line with no transaction\n"
    assert parse_transactions(text) == []


# ---------- Classifier tests ----------

def test_rule_classifier_food():
    assert rule_classify("SWIGGY ORDER 450") == "Food"


def test_rule_classifier_transport():
    assert rule_classify("UBER RIDE TO AIRPORT") == "Transport"


def test_rule_classifier_atm():
    assert rule_classify("ATM WITHDRAWAL SELF-SWITCH") == "ATM"


def test_ml_fallback_on_unknown_description():
    model = train_ml_classifier()
    txns = [{"description": "some totally unseen merchant xyz", "debit": 100, "credit": None}]
    classified = classify_transactions(txns, model)
    assert "category" in classified[0]
    assert classified[0]["category"] is not None


if __name__ == "__main__":
    test_extract_account_info()
    test_extract_account_info_bare_name_with_address()
    test_extract_account_info_account_name_label()
    test_parse_debit_and_credit_by_balance_delta()
    test_empty_text_returns_no_transactions()
    test_line_without_date_is_skipped()
    test_rule_classifier_food()
    test_rule_classifier_transport()
    test_rule_classifier_atm()
    test_ml_fallback_on_unknown_description()
    print("All tests passed!")