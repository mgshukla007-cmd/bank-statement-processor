import re


def _clean_name(name):
    """Normalize whitespace and strip trailing punctuation."""
    if not name:
        return None
    name = re.sub(r"\s+", " ", name).strip(" .,-:\t")
    if len(name) < 3 or len(name) > 60:
        return None
    if any(bad in name.lower() for bad in [
        "account", "statement", "bank", "branch", "customer id",
        "address", "summary", "page", "date",
    ]):
        return None
    return name


def _extract_holder_by_label(text):
    """Try explicit labels first: 'Account Holder:', 'Account Name:', 'Customer Name:', 'Name:'."""
    labels = [
        r"Account\s*Holder(?:\s*Name)?",
        r"Account\s*Name",
        r"Customer\s*Name",
        r"A/?C\s*Holder",
        r"Primary\s*Holder",
        r"Name",
    ]
    for label in labels:
        pat = rf"{label}\s*[:\-]?\s*([A-Za-z][A-Za-z\.\-' ]{{2,55}}?)(?=\n|$|\s{{2,}}|\d{{3,}})"
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            cleaned = _clean_name(m.group(1))
            if cleaned:
                return cleaned
    return None


def _extract_holder_by_bare_line(text):
    """
    Fallback: find a line that looks like a person's name and is
    typically above an address block.
    """
    lines = [ln.strip() for ln in text.split("\n")]
    address_kw = re.compile(
        r"\b(road|street|st\.|avenue|ave|lane|drive|dr\.|nagar|colony|"
        r"city|state|zip|pin|india|pincode|floor|building|apartment|"
        r"po box|near|landmark)\b",
        re.IGNORECASE,
    )
    name_pat = re.compile(
        r"^(?:(?:MR|MRS|MS|DR|SHRI|SMT|KUM)\.?\s+)?"
        r"([A-Z][A-Za-z\.\-']*(?:\s+[A-Z][A-Za-z\.\-']*){1,4})$"
    )

    for i, line in enumerate(lines):
        if len(line) < 5 or len(line) > 60:
            continue
        if address_kw.search(line):
            continue
        m = name_pat.match(line)
        if not m:
            continue

        # Bonus: check next 6 lines contain something address-like
        window = " ".join(lines[i + 1 : i + 7])
        if address_kw.search(window):
            return _clean_name(line)

    return None


def extract_account_info(text):
    """
    Extract account holder name, account number, and IFSC.
    Uses a cascade: labeled match -> bare-line heuristic -> None.
    """
    info = {"account_holder": None, "account_number": None, "ifsc": None}

    # --- Account holder ---
    info["account_holder"] = _extract_holder_by_label(text) or _extract_holder_by_bare_line(text)

    # --- Account number ---
    acct_patterns = [
        r"(?:Account\s*(?:Number|No\.?|#)|A/?C\s*(?:Number|No\.?|#))\s*[:\-]?\s*([Xx\d]{6,20})",
        r"(?:Primary\s*Account\s*Number)\s*[:\-]?\s*([Xx\d]{6,20})",
    ]
    for pat in acct_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            info["account_number"] = m.group(1).strip()
            break

    # --- IFSC (Indian banks) ---
    ifsc_patterns = [
        r"\bIFSC\s*(?:Code)?\s*[:\-]?\s*([A-Z]{4}0[A-Z0-9]{6})",
        r"\b([A-Z]{4}0[A-Z0-9]{6})\b",
    ]
    for pat in ifsc_patterns:
        m = re.search(pat, text)
        if m:
            info["ifsc"] = m.group(1).strip()
            break

    return info


# Regex patterns for transaction parsing
DATE_PATTERN = r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})"
AMOUNT_PATTERN = r"([\d,]+\.\d{2})"


def parse_transactions(text):
    """
    Parses transactions from extracted text.
    Uses balance-delta logic to determine debit vs credit.
    """
    transactions = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        date_match = re.search(DATE_PATTERN, line)
        if not date_match:
            continue

        amounts = re.findall(AMOUNT_PATTERN, line)
        if len(amounts) < 2:
            continue

        desc_start = date_match.end()
        first_amt_pos = line.find(amounts[0], desc_start)
        if first_amt_pos == -1:
            continue

        description = line[desc_start:first_amt_pos].strip()
        description = re.sub(r"^[\s\|\-:]+", "", description)
        description = re.sub(
            r"^(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})\s*",
            "",
            description,
        ).strip()

        try:
            balance = float(amounts[-1].replace(",", ""))
            txn_amount = float(amounts[-2].replace(",", ""))
        except ValueError:
            continue

        transactions.append({
            "date": date_match.group(1),
            "description": description if description else "N/A",
            "amount": txn_amount,
            "balance": balance,
            "debit": None,
            "credit": None,
        })

    # Second pass: debit vs credit by balance direction
    prev_balance = None
    for txn in transactions:
        desc = txn["description"]
        is_credit_kw = bool(re.search(r"(credit|deposit|received|refund|reversal|\bcr\b)", desc, re.IGNORECASE))
        is_debit_kw = bool(re.search(r"(debit|withdraw|paid|purchase|\bdr\b)", desc, re.IGNORECASE))

        if prev_balance is not None:
            delta = txn["balance"] - prev_balance
            if delta > 0:
                txn["credit"] = txn["amount"]
            else:
                txn["debit"] = txn["amount"]
        else:
            if is_credit_kw and not is_debit_kw:
                txn["credit"] = txn["amount"]
            else:
                txn["debit"] = txn["amount"]

        prev_balance = txn["balance"]
        del txn["amount"]

    return transactions