# NACHA File Format Specification

## Overview

NACHA (National Automated Clearing House Association) is the governing body for the ACH (Automated Clearing House) network in the United States. The NACHA file format is the standard used for creating ACH payment files.

**Document Version:** 2025
**ACH Operating Rules:** Effective September 2025

---

## Table of Contents

1. [File Structure](#file-structure)
2. [Record Types](#record-types)
3. [Record Layouts](#record-layouts)
4. [Data Validation Rules](#data-validation-rules)
5. [Practical Examples](#practical-examples)
6. [Reference Resources](#reference-resources)

---

## File Structure

A NACHA file consists of records arranged in a specific hierarchical structure:

```
File Header Record (1 record)
├── Batch Header Record
│   ├── Entry Detail Record (1 to n)
│   └── Batch Control Record
├── Batch Header Record
│   ├── Entry Detail Record (1 to n)
│   └── Batch Control Record
└── File Control Record (1 record)
```

### Record Structure

- **Record Length:** 94 characters (positions 1-94)
- **Record Type Code:** Position 1 (identifies record type: 1, 5, 6, 7, 8, or 9)
- **Character Set:** ASCII alphanumeric
- **Field Padding:** Numeric fields left-justified and zero-filled; alphanumeric fields left-justified and space-filled

---

## Record Types

| Record Type | Code | Description |
|---|---|---|
| File Header Record | 1 | Identifies the file and transmitting institution |
| Batch Header Record | 5 | Identifies the batch of entries |
| Entry Detail Record | 6 | Contains payment/receipt information |
| Addenda Record | 7 | Additional payment-related information (optional) |
| Batch Control Record | 8 | Provides control totals for a batch |
| File Control Record | 9 | Provides control totals for entire file |

---

## Record Layouts

### Record Type 1: File Header Record

**Record Identifier:** `1` (position 1)

| Field | Position | Length | Type | Description |
|---|---|---|---|---|
| Record Type Code | 1 | 1 | Numeric | `1` |
| Priority Code | 2-3 | 2 | Numeric | `00` (standard) |
| Immediate Destination | 4-12 | 9 | Numeric | Receiving bank's routing number (with leading space) |
| Immediate Origin | 13-21 | 9 | Numeric | Originating bank's routing number (with leading space) |
| File Creation Date | 22-27 | 6 | Numeric | YYMMDD format |
| File Creation Time | 28-31 | 4 | Numeric | HHMM format (optional, usually spaces) |
| File ID Modifier | 32 | 1 | Alphanumeric | Usually `A` |
| Record Size Code | 33-35 | 3 | Numeric | `094` (standard file record length) |
| Blocking Factor | 36-37 | 2 | Numeric | `10` (10 records per block) |
| Format Code | 38 | 1 | Alphanumeric | `1` for US data |
| Immediate Destination Name | 39-62 | 23 | Alphanumeric | Receiving bank's name |
| Immediate Origin Name | 63-86 | 23 | Alphanumeric | Originating bank/company name |
| Reference Code | 87-94 | 8 | Alphanumeric | File reference code (spaces) |

**Example:**
```
101 121000248 123456789230214180555A094101YourBank          Your Company       
```

---

### Record Type 5: Batch Header Record

**Record Identifier:** `5` (position 1)

| Field | Position | Length | Type | Description |
|---|---|---|---|---|
| Record Type Code | 1 | 1 | Numeric | `5` |
| Service Class Code | 2-3 | 2 | Numeric | `200` (Mixed), `220` (Credits), `225` (Debits) |
| Company Name | 4-20 | 16 | Alphanumeric | Company originating the batch |
| Company Discretionary Data | 21-40 | 20 | Alphanumeric | Optional company reference |
| Company Identification | 41-48 | 8 | Alphanumeric | Company's ID (usually EIN) |
| Standard Entry Class (SEC) | 49-51 | 3 | Alphanumeric | `PPD`, `CCD`, `CTX`, `ACK`, `ATX`, `STP`, `TRC`, `TRX` |
| Entry Effective Date | 52-57 | 6 | Numeric | YYMMDD (when entries become effective) |
| Settlement Date | 58-60 | 3 | Numeric | JJJ (Julian date) |
| Originator Status Code | 61 | 1 | Numeric | `0` (originating depository financial institution) |
| Originating DFI ID | 62-68 | 7 | Numeric | First 8 digits of routing number |
| Batch Number | 69-72 | 4 | Numeric | Sequential batch number (1-9999) |
| Entry/Addenda Indicator | 73 | 1 | Numeric | `0` (no addenda), `1` (addenda present) |
| Field Inclusion Indicator | 74-76 | 3 | Numeric | Not typically used |
| Company Descriptive Date | 77-79 | 3 | Numeric | JJJ (Julian date) |
| Effective Entry Date | 80-85 | 6 | Numeric | YYMMDD |
| Reserved | 86-94 | 9 | Alphanumeric | Spaces |

**Example:**
```
520PayrollCompany     00000000123456780PPD250216025000Company Inc.       001000000
```

---

### Record Type 6: Entry Detail Record

**Record Identifier:** `6` (position 1)

| Field | Position | Length | Type | Description |
|---|---|---|---|---|
| Record Type Code | 1 | 1 | Numeric | `6` |
| Transaction Code | 2-3 | 2 | Numeric | `22` (deposit/credit), `27` (withdrawal/debit), `32` (corr. debit), `37` (corr. credit) |
| Receiving DFI ID | 4-11 | 8 | Numeric | Receiving financial institution routing number |
| Check Digit | 12 | 1 | Numeric | Check digit of DFI ID |
| DFI Account Number | 13-29 | 17 | Alphanumeric | Receiver's account number (left-justified, space-filled) |
| Amount | 30-39 | 10 | Numeric | Amount in cents (zero-filled) |
| Individual ID Number | 40-54 | 15 | Alphanumeric | Receiver ID or reference number |
| Individual Name | 55-76 | 22 | Alphanumeric | Receiver's name |
| Discretionary Data | 77-78 | 2 | Alphanumeric | Usually spaces |
| Addenda Indicator | 79 | 1 | Numeric | `0` (no addenda), `1` (addenda present) |
| Trace Number | 80-94 | 15 | Numeric | Unique trace:originating routing (9) + sequence (6) |

**Example:**
```
622121000219123456789   000000050000Employee123456Joe Customer                  0000012100021001234
```

---

### Record Type 7: Addenda Record

**Record Identifier:** `7` (position 1)

| Field | Position | Length | Type | Description |
|---|---|---|---|---|
| Record Type Code | 1 | 1 | Numeric | `7` |
| Addenda Type Code | 2-3 | 2 | Numeric | `05` (CCD), `01` (PPD), `02` (CTX) |
| Payment-Related Information | 4-83 | 80 | Alphanumeric | Additional transaction details |
| Sequence Number | 84-87 | 4 | Numeric | Addenda sequence number (0001-9999) |
| Entry Detail Sequence Number | 88-94 | 7 | Numeric | Corresponding entry detail sequence |

**Example:**
```
705Invoice details and reference information...                                  000100000001
```

---

### Record Type 8: Batch Control Record

**Record Identifier:** `8` (position 1)

| Field | Position | Length | Type | Description |
|---|---|---|---|---|
| Record Type Code | 1 | 1 | Numeric | `8` |
| Service Class Code | 2-3 | 2 | Numeric | (same as batch header) |
| Entry/Addenda Count | 4-9 | 6 | Numeric | Number of entries + addenda in batch |
| Entry Hash | 10-19 | 10 | Numeric | Hash of receiving DFI IDs (first 8 digits) |
| Total Debit Entry Dollar Amount | 20-29 | 10 | Numeric | Sum of all debits in cents |
| Total Credit Entry Dollar Amount | 30-39 | 10 | Numeric | Sum of all credits in cents |
| Company Identification | 40-47 | 8 | Alphanumeric | (same as batch header) |
| Message Authentication Code | 48-67 | 20 | Alphanumeric | Space-filled (optional security code) |
| Reserved | 68-72 | 5 | Alphanumeric | Spaces |
| Originating DFI ID | 73-79 | 7 | Numeric | (same as batch header) |
| Batch Number | 80-83 | 4 | Numeric | (same as batch header) |
| Reserved | 84-94 | 11 | Alphanumeric | Spaces |

**Example:**
```
820000002000012100021000000050000000000000500012100001234567         0000001
```

---

### Record Type 9: File Control Record

**Record Identifier:** `9` (position 1)

| Field | Position | Length | Type | Description |
|---|---|---|---|---|
| Record Type Code | 1 | 1 | Numeric | `9` |
| Batch Count | 2-7 | 6 | Numeric | Number of batches in file |
| Block Count | 8-13 | 6 | Numeric | Number of blocks in file |
| Entry/Addenda Count | 14-19 | 6 | Numeric | Total entries + addenda in file |
| Entry Hash | 20-29 | 10 | Numeric | Hash of all receiving DFI IDs |
| Total Debit Entry Dollar Amount | 30-39 | 10 | Numeric | Sum of all debits in cents |
| Total Credit Entry Dollar Amount | 40-49 | 10 | Numeric | Sum of all credits in cents |
| Reserved | 50-94 | 45 | Alphanumeric | Spaces |

**Example:**
```
900000001000001000000002000012100021000000050000000000000500        
```

---

## Data Validation Rules

### General Rules

1. **Record Length:** All records must be exactly 94 characters
2. **Field Padding:**
   - Numeric fields: Left-justified, zero-filled
   - Alphanumeric fields: Left-justified, space-filled
3. **Character Set:** ASCII characters only (01-127)
4. **Date Format:** YYMMDD (positions refer to 2000-2099)

### Specific Validations

#### Routing Number Check Digit

The 9th position of the routing number (Receiving DFI ID or Originating DFI ID) contains a check digit calculated using the NACHA algorithm:

```
Check Digit = (7 × d1 + 3 × d2 + 9 × d3 + 7 × d4 + 3 × d5 + 9 × d6 + 7 × d7 + 3 × d8) mod 10
```

#### Entry Hash

Calculate hash by summing the first 8 digits of each receiving DFI ID and taking mod 10,000,000,000 (10 billion):

```
Entry Hash = Σ(first 8 digits of each DFI ID) mod 10,000,000,000
```

#### Amount Validation

- Amounts must be non-negative
- Amounts are in cents (0-9,999,999,999)
- Total credits = Total debits for a valid file

### Transaction Codes

| Code | Description | Debit/Credit |
|---|---|---|
| 22 | Demand Deposit Account (credit) | Credit |
| 27 | Demand Deposit Account (debit) | Debit |
| 32 | Savings Account (debit) | Debit |
| 37 | Savings Account (credit) | Credit |
| 42 | Checking Account (debit) | Debit |
| 47 | Checking Account (credit) | Credit |

### Service Class Codes

| Code | Description |
|---|---|
| 200 | Mixed debits and credits |
| 220 | Credits only |
| 225 | Debits only |

### Standard Entry Class (SEC) Codes

| Code | Description |
|---|---|
| PPD | Pre-authorized Payments and Deposits (debits/credits to consumer accts) |
| CCD | Corporate Credit or Debit (debits/credits to corporate/government accts) |
| CTX | Corporate Trade Exchange |
| ACK | Acknowledgment Entries |
| ATX | Acknowledgment and Transaction |
| STP | Settlement Entries |
| TRC | Treasury Management Information |
| TRX | Treasury Tax Information |

---

## Practical Examples

### Example 1: Simple Direct Deposit File

**File Structure:**
- 1 Batch (payroll)
- 2 Entries (2 employees)
- No addenda

**Records:**

```
1 121000248 123456789230214180555A094101YourBank          Your Company       
520Payroll Compan 00000000123456780PPD250216025000CompanyNameHere          0000010
622121000219123456789   000000050000Employee001    John Smith                 0000012100021001234
622987654321987654321   000002500000Employee002    Jane Doe                   0000012100021002344
820000002000012100021000000300000000000025012100001234567         0000010
900000001000001000000004000011121021000000300000000000025001        
```

### Example 2: With Addenda Record

```
1 121000248 123456789230214180555A094101YourBank          Your Company       
520Payroll Compan 00000000123456780PPD250216025000CompanyNameHere          0000010
622121000219123456789   000000050000Employee001    John Smith        10000012100021001234
705Invoice 001: Details for transaction tracing and accounting purposes     000100000001
820000002000012100021000000200000000000050012100001234567         0000010
900000001000001000000003000011121021000000200000000000050001        
```

---

## Key Considerations for Implementation

### File Numbering
- File ID Modifier should increment with each file (A, B, C, ... Z, 0, 1, ... 9)
- Batch numbers should be sequential within a file (1-9999)
- Entry Trace Numbers must be unique within each originating institution

### Date Processing
- Entry Effective Date = when the payment becomes effective
- Settlement Date = when funds are settled (usually 0, 1, or 2 days)
- File Creation Date = current date when file is generated

### Record Counts and Hashes
- Entry/Addenda count in Batch Control must match actual entries + addenda
- Entry Hash in File Control must match sum of all Batch Control hashes
- Total amounts must balance (sum of debits = sum of credits)

### STP (Same-Time Processing)
- For Same-Day ACH, appropriate effective dates and settling dates must be used
- Fees may apply for STP entries

---

## Reference Resources

### Official NACHA Documentation
- NACHA Operating Rules & Guidelines (available at https://www.nacha.org/)
- ACH Network Rules Updates

### Key Standards
- ANSI X12 (for structured data within ACH)
- ISO 20022 (emerging standard for payment information)

### Additional Information
- Contact NACHA directly for certification and requirements
- Visit https://www.nacha.org/ for official documentation
- ACH Quick Start Tool: https://www.nacha.org/

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-02-14 | Initial specification document |

**Last Updated:** February 14, 2026
