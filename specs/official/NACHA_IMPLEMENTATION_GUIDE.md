# NACHA Payment Implementation Guide

## Overview

This guide provides practical implementation details for creating and processing NACHA files for ACH payment transactions.

---

## Common Use Cases

### 1. Payroll Direct Deposit (PPD)

**Purpose:** Distribute employee paychecks via ACH

**Configuration:**
- SEC Code: `PPD` (Pre-authorized Payments and Deposits)
- Service Class: `220` (Credits Only - for direct deposits)
- Entry Effective Date: Next business day
- Settlement: 0-1 days

**File Example:**
```
Company sends employee payment details to employees' banks
Benefits: Fast, reliable, cost-effective payroll processing
```

### 2. Corporate-to-Corporate Payments (CCD)

**Purpose:** Transfer funds between business accounts

**Configuration:**
- SEC Code: `CCD` (Corporate Credit or Debit)
- Service Class: `200` (Mixed debits/credits) or `220`/`225` for single type
- Entry Effective Date: Same or next business day
- Settlement: 1 day

**Use Cases:**
- Vendor payments
- Intercompany transfers
- B2B invoice settlement

### 3. Same-Day ACH (STP)

**Purpose:** Faster payment processing (within hours)

**Configuration:**
- SEC Code: `PPD` or `CCD`
- Effective Date: Same day
- Settlement: 0 (same-day settlement)
- Special handling required

**Note:** Same-day ACH may have higher fees and specific cutoff times.

### 4. Account Verification

**Purpose:** Validate account numbers before processing

**Configuration:**
- SEC Code: `ACK` (Acknowledgment)
- Service Class: `200` or `220`
- No actual fund transfer

---

## Field Validation Rules

### Routing Number Validation

**Format:** 9 digits
- First 4 digits: Federal Reserve Routing Symbol
- Next 4 digits: ABA Institution Identifier
- Last digit: Check digit (calculated)

**Check Digit Algorithm:**
```python
def calculate_check_digit(routing_number_8digits):
    d1, d2, d3, d4, d5, d6, d7, d8 = [int(x) for x in str(routing_number_8digits).zfill(8)]
    check = (7*d1 + 3*d2 + 9*d3 + 7*d4 + 3*d5 + 9*d6 + 7*d7 + 3*d8) % 10
    return check
```

### Account Number Validation

- **Length:** 1-17 characters
- **Format:** Alphanumeric (letters and numbers)
- **Space Filling:** Right-padded with spaces in NACHA record
- **Validation:** Bank-specific (format varies by institution)

### Amount Validation

- **Range:** 0 to $99,999,999.99
- **Format:** Integer (in cents) in NACHA file
- **Example:** $1,234.56 = 123456 (cents)
- **Padding:** Zero-filled to 10 digits

### Date Validation

**File Creation Date (YYMMDD):**
```
Valid Range: 000101 - 991231
Century Rule: 00-29 = 2000-2029, 30-99 = 1930-1999
Example: 260214 = February 14, 2026
```

**Entry Effective Date:**
- Cannot be past (typically 1-2 days in future)
- Must be business day (no weekends/holidays in most cases)
- Coordinated with settlement date

### Company Identification (EIN)

- **Format:** 9-digit Employer Identification Number (XX-XXXXXXX)
- **Storage:** Without dashes in NACHA file (9 characters)
- **Example:** EIN "12-3456789" stored as "123456789"

### Individual ID Number

- **Format:** Alphanumeric (up to 15 characters)
- **Purpose:** Receiver's ID, invoice number, or custom reference
- **Left-justified, space-filled**

### Individual Name

- **Format:** Alphanumeric (up to 22 characters)
- **Purpose:** Receiver's name or identifier
- **Left-justified, space-filled**
- **Special Characters:** Limited to standard ASCII alphanumeric + spaces

---

## Transaction Type Selection

### Debit Transactions (Taking Money)

| Code | Account Type | Use Case |
|---|---|---|
| 27 | Demand Deposit | Business checking |
| 32 | Savings Account | Business savings |
| 42 | Checking Account | Consumer checking |

### Credit Transactions (Sending Money)

| Code | Account Type | Use Case |
|---|---|---|
| 22 | Demand Deposit | Business checking |
| 37 | Savings Account | Business/Consumer savings |
| 47 | Checking Account | Consumer checking |

---

## File Totals and Controls

### Balance Validation

For a valid NACHA file:
```
Total Credits = Total Debits

OR

Net amount = 0 (from both debit and credit transactions)
```

### Entry Count

**File Entry Count = Sum of:**
- All entry detail records (type 6)
- All addenda records (type 7)

**Example:**
```
Batch 1: 10 entries + 2 addenda = 12
Batch 2: 5 entries + 0 addenda = 5
File Total: 17 entry/addenda records
```

### Hash Calculation

**Entry Hash Purpose:** Verification that DFI routing numbers weren't altered

**Calculation:**
```
Hash = Σ(first 8 digits of each receiving DFI ID) mod 10,000,000,000
```

**Example:**
```
Entry 1 DFI: 121000248 → use 12100024
Entry 2 DFI: 987654321 → use 98765432
Entry 3 DFI: 121000248 → use 12100024

Hash = (12100024 + 98765432 + 12100024) mod 10,000,000,000
     = 122,965,480
```

---

## Addenda Records (Type 7)

### When to Use Addenda

Addenda records provide additional information and are used for:
- Payment descriptions (CCD)
- Invoice details
- Reference information
- Remittance advice

### Addenda Type Codes

| Type | Code | SEC Code | Purpose |
|---|---|---|---|
| CCD Addenda | 05 | CCD, CTX | Corporate payment details |
| PPD Addenda | 01 | PPD | Payment description |

### Addenda in Entry Details

**Setting Addenda Indicator:**
- If addenda records follow an entry: Set to `1` in Entry Detail Record (position 79)
- If no addenda: Set to `0`

**Sequence:**
```
Entry Detail Record (Addenda Indicator = 1)
  ↓
Addenda Record 1 (Type 7)
  ↓
Entry Detail Record (Addenda Indicator = 0)
  ↓
Entry Detail Record (Addenda Indicator = 1)
  ↓
Addenda Record 1 (Type 7)
```

---

## Settlement and Processing Dates

### ACH Processing Timeline

```
Day 0: File Created
       ↓
Day 1: File Transmitted & Processed
       ↓
Day 1-2: Settlement (based on effective date)
       ↓
Day 2-3: Funds Available in Receiver's Account
```

### Settlement Date Codes

- `0` = Same-day settlement (STP)
- `1` = Next-day settlement (standard)
- `2` = Two-day settlement

### Entry Effective Date Rules

- Usually 1 business day from file creation
- Cannot exceed 30 days in future
- Coordinated with batch settlement date

---

## Common Errors and Prevention

### Error Type 1: Hash Mismatch

**Cause:** Incorrect calculation of entry hash or modified routing numbers

**Prevention:**
- Verify all routing numbers are valid
- Recalculate hash after any modifications
- Validate routing number format (9 digits with valid check digit)

### Error Type 2: Unbalanced Amounts

**Cause:** Total debits ≠ Total credits

**Prevention:**
- Maintain separate debit and credit totals
- Verify totals before file generation
- Double-check amount conversions ($ to cents)

### Error Type 3: Invalid Dates

**Cause:** Future dates, weekends, or bad formatting

**Prevention:**
- Validate date is within acceptable range
- Check for business day (exclude weekends/holidays)
- Use consistent YYMMDD format

### Error Type 4: Record Length

**Cause:** Records not exactly 94 characters

**Prevention:**
- Pad all fields correctly
- Validate final record length
- Check for extra spaces or missing padding

### Error Type 5: Duplicate Trace Numbers

**Cause:** Same trace number used for multiple entries

**Prevention:**
- Generate unique trace numbers sequentially
- Format: Originating Routing (9 digits) + Sequence (6 digits)
- Reset sequence for each originating institution

---

## Batch Processing Rules

### Batch Homogeneity

Each batch should contain:
- Same Service Class Code
- Same SEC Code
- Same Originating Institution

### Single-Batch File

For simple payroll or B2B transfers, one batch per file is typically sufficient.

### Multi-Batch File

For complex scenarios with mixed transaction types:
- Each batch must have separate Header (Type 5) and Control (Type 8)
- File Header (Type 1) and File Control (Type 9) summarize all batches

---

## Implementation Checklist

- [ ] Validate all input data (account numbers, routing numbers, amounts)
- [ ] Calculate correct check digits for routing numbers
- [ ] Generate unique trace numbers for each entry
- [ ] Set appropriate transaction codes (22-47)
- [ ] Calculate entry hashes correctly
- [ ] Verify total debits = total credits
- [ ] Count entries and addenda accurately
- [ ] Ensure all records are exactly 94 characters
- [ ] Use valid YYMMDD dates
- [ ] Set correct SEC codes for transaction type
- [ ] Validate company identification (EIN)
- [ ] Test file with ACH processor before production

---

## Resources

- NACHA Operating Rules: https://www.nacha.org/
- Fed ACH Directory: https://www.frbservices.org/
- ISO 20022 Standard: https://www.iso20022.org/

---

**Last Updated:** February 14, 2026
