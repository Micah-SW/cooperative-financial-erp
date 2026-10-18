# Cooperative Financial Management ERP — Business Rule Classification & Open Questions Register

> **Document Status**: Authoritative Classification Reference  
> **Milestone**: Chapter 02 — Repair the Foundations  
> **Purpose**: Distinguish Confirmed Cooperative Requirements from Unresolved Business Decisions and Proposed Technical Safeguards.  

---

## 1. Classification Framework

To protect financial and business integrity, every operational and domain rule in the Cooperative ERP is explicitly categorized into one of three classifications:

1. **CONFIRMED BUSINESS REQUIREMENT**:
   - Authoritative policy established and verified by the cooperative union.
   - Non-negotiable domain rules that the ERP software must faithfully reflect.
2. **UNRESOLVED BUSINESS DECISION**:
   - Open legal, governance, financial, or accounting questions that the cooperative has **not yet decided**.
   - Proposed implementations or software guardrails for these questions **must not be treated as approved cooperative policy**.
3. **PROPOSED TECHNICAL SAFEGUARD**:
   - An engineering safety mechanism (e.g., database constraint, state machine restriction, feature flag, isolated ledger stream) introduced to prevent accidental data corruption or premature financial execution while a business decision remains pending.
   - Safeguards exist solely to keep data safe; they do not dictate or imply cooperative policy.

---

## 2. Summary of Confirmed Cooperative Requirements

The following requirements are established facts for the cooperative union:

1. **Membership Base**: The cooperative has approximately 150 existing members, and membership is currently closed.
2. **Share Capital**: Each member currently holds 12 shares associated with a paid-up balance of ETB 60,000, based on a current nominal share value of ETB 5,000 per share (subject to future cooperative vote).
3. **Recurring Contributions**: Under the current operational arrangement, members contribute ETB 300 toward member/project equity and ETB 50 toward union operating expenses.
4. **Deposit Channel**: Members deposit funds directly into the cooperative union's commercial bank account.
5. **Ownership of Investment Returns**: Investment and property profits do **not** belong to individual members. Cooperative income supports normal union operating expenses, and the remaining rental-project income is intended for the mall project.
6. **Member Exit & Record Retention**: Members may leave the cooperative, receive their refundable money under the cooperative's applicable rules, and have their shares extinguished. Their historical records must remain available and cannot be deleted.

---

## 3. Comprehensive Register: UBR-1 through UBR-18

| ID | Title | Classification | Summary & Cooperative Stance | Proposed Technical Safeguard |
|---|---|---|---|---|
| **UBR-1** | Exit Payout Formula & Waiting Period | **UNRESOLVED BUSINESS DECISION** | Confirmed: Exiting members receive refundable money under cooperative rules. Unresolved: Deductions, deductions for shared project losses, payout installment schedule, waiting periods. | Record raw historical balances and transactions; payout calculation logic is deferred; no automated deduction or payout calculations until cooperative enacts policy. |
| **UBR-2** | Contribution Frequency & Arrears Enforcement | **UNRESOLVED BUSINESS DECISION** | Confirmed: Current contribution is ETB 300 + ETB 50. Unresolved: Mandatory monthly due dates, grace periods, default penalties, suspension triggers. | Record contributions with transaction dates as deposits occur; do not enforce automated penalties, lockouts, or automated arrears calculations in software. |
| **UBR-3** | Individual Profit / Dividend Distribution | **CONFIRMED BUSINESS REQUIREMENT** | Confirmed: Profits from cooperative investments and properties belong exclusively to the union. Zero profit/dividends distributed to individual members. | Ledger schema strictly prohibits credit transactions from rental/investment funds into member equity accounts. |
| **UBR-4** | Share-Tied Voting Rights | **UNRESOLVED BUSINESS DECISION** | Confirmed: Cooperative governance topic. Unresolved: One-member-one-vote vs share-weighted voting. | Excluded entirely from financial ERP scope. |
| **UBR-5** | Member Loan Facilities | **UNRESOLVED BUSINESS DECISION** | Unresolved: Whether member equity may collateralize internal loans. | Excluded entirely from v1 financial schema. |
| **UBR-6** | Accounting Currency | **CONFIRMED BUSINESS REQUIREMENT** | Confirmed: All financial accounts, shares, and contributions operate strictly in Ethiopian Birr (ETB). | Monetary fields enforce numeric decimal representation in ETB. Configurable currency code preserved for future extensibility without multi-currency logic. |
| **UBR-7** | Interest Accrual on Member Balances | **CONFIRMED BUSINESS REQUIREMENT** | Confirmed: Member contribution balances do not accrue interest. The cooperative is not a commercial bank. | Zero interest accrual logic or transactions exist in the ledger engine. |
| **UBR-8** | Partial Withdrawal Without Exiting | **UNRESOLVED BUSINESS DECISION** | Unresolved: Whether an active member may withdraw any equity without terminating membership. | Feature is disabled by default via `PARTIAL_WITHDRAWAL_ALLOWED = false` config flag; API blocks partial withdrawals unless explicitly enabled. |
| **UBR-9** | Bank Deposit Verification & Approval Workflow | **UNRESOLVED BUSINESS DECISION** | Confirmed: Members deposit directly into bank accounts. Unresolved: Single vs dual approval, verification timeframe, handling of illegible slips. | Two-stage workflow (`RECORDED` → `VERIFIED`) requiring manual entry of bank slip reference by authorized treasurer/admin before funds are marked verified. |
| **UBR-10** | Fiscal Year Definition | **UNRESOLVED BUSINESS DECISION** | Unresolved: Gregorian calendar year vs Ethiopian fiscal year (Hamle 1 - Sene 30). | Store dates as standard ISO timestamps; parameterize reporting queries with explicit date ranges (`start_date`, `end_date`) to remain fiscal-year agnostic. |
| **UBR-11** | Member Suspension Status & Sanctions | **UNRESOLVED BUSINESS DECISION** | Unresolved: Grounds for suspension, impact on ongoing contribution duties, and access rights. | Enum retains `SUSPENDED` value for future schema compatibility, but zero automated transition workflows or business logic are attached to it. |
| **UBR-12** | Maximum Contribution Limits | **UNRESOLVED BUSINESS DECISION** | Unresolved: Whether voluntary member contributions exceeding ETB 300/50 are permitted, and how surplus is treated. | Software validates member vs operating split but enforces no arbitrary maximum contribution ceiling. |
| **UBR-13** | Expenditure Approval Thresholds | **UNRESOLVED BUSINESS DECISION** | Unresolved: Tiered expenditure authorization levels (e.g. board sign-off thresholds for expenses exceeding specific amounts). | Direct recording by `ADMIN` or `TREASURER` with mandatory receipt reference and fund allocation; tiered multi-signature workflows deferred. |
| **UBR-14** | Share Capital vs. Recurring Contribution Balance Relationship | **UNRESOLVED BUSINESS DECISION** | Confirmed: 12 shares @ ETB 5,000 = ETB 60,000; recurring contribution is ETB 300 + ETB 50. Unresolved: Whether initial ETB 60,000 share capital merges with recurring ETB 300 contributions into a single refundable balance, or remains distinct. | Maintain `coop.shares` and `coop.contributions` as strictly distinct tables and separate ledger streams; do not implement automated opening-balance merging, cumulative balance calculations, or combined payout workflows until formally resolved by the cooperative. |
| **UBR-15** | Historical Opening Balance Import & Cut-Off Protocol | **UNRESOLVED BUSINESS DECISION** | Confirmed: ~150 founding members have historical records. Unresolved: Cut-off reconciliation date, format of opening balance ledger entries (lump-sum vs detailed retroactive). | No automated opening-balance import scripts or ledger seeding are implemented in software; schema supports `OPENING_BALANCE` transaction type when authoritative cut-off figures are formally approved. |
| **UBR-16** | Direct Bank Deposit Verification & Unidentified Inflows | **UNRESOLVED BUSINESS DECISION** | Confirmed: Members deposit directly into cooperative bank account. Unresolved: Legal procedure and timeframe for identifying unreferenced bank deposits. | Unidentified bank deposits are never automatically assigned to any member; manual cross-referencing with physical slips is mandatory before verifying. |
| **UBR-17** | Member Exit Permanence vs. Readmission Policy | **UNRESOLVED BUSINESS DECISION** | Confirmed: Members can leave, have shares extinguished, receive refundable money under applicable rules, and historical records remain available. Unresolved: Whether exit is permanently irreversible by cooperative policy, or whether an exited member could later be readmitted. | In the v1 software state machine, member exit transition `ACTIVE` → `EXITED` is strictly one-way without automated reactivation routes. Historical records are preserved permanently (never deleted). This technical constraint is a safeguard to prevent accidental reactivation and must NOT be misconstrued as an approved cooperative policy prohibiting readmission. |
| **UBR-18** | Rental Income Allocation, Mall Project Funding & Reserve Fund | **UNRESOLVED BUSINESS DECISION** *(with Confirmed Intent)* | Confirmed: Investment profits do not belong to individual members; cooperative income supports normal union expenses, and remaining rental-project income is intended for the mall project. Unresolved: Whether a formal "Reserve Fund" is mandated by bylaws, and the exact formula/split for allocating rental income. | Isolate rental earnings from member equity ledgers. Store rental income in dedicated cooperative accounts without distributing dividends to members. Fund allocation ratios between operating expenses and project construction remain configurable rather than hardcoded in application logic. |

---

## 4. Deep-Dive on Critical Review Areas

### 4.1 Member Exit Permanence vs. Readmission Policy (UBR-17)
- **Confirmed Cooperative Requirement**:
  - Members possess the legal right to leave the cooperative.
  - Upon leaving, their shares are extinguished and they receive their refundable money in accordance with the cooperative's applicable rules.
  - Their historical financial records, contribution logs, and transaction trails must remain permanently available for audit and accounting integrity.
- **Unresolved Business Decision**:
  - The cooperative has **not decided** whether an exit is permanently final under union bylaws, or whether an exited member may apply for readmission at a later date if membership is reopened.
  - If readmission is ever permitted: What happens to their historical `member_number`? Are past extinguished shares reinstated or newly repurchased? Does previous tenure count toward seniority?
- **Proposed Technical Safeguard (v1 Software)**:
  - The software's state machine enforces a strict one-way transition: `ACTIVE` → `EXITED`.
  - Exited member records are never physically or soft-deleted from `coop.members`.
  - The software provides no automated self-serve or admin "re-activate" button in v1.
  - **Important Clarification**: This technical guardrail exists solely to prevent accidental state flips or unauthorized reactivation. It is **not** an approved cooperative business policy banning readmission.

---

### 4.2 Direct Bank Deposit Verification & Approval Process (UBR-9 & UBR-16)
- **Confirmed Cooperative Requirement**:
  - Members deposit funds directly into the cooperative's commercial bank account (e.g. CBE) via bank branch, mobile banking, or transfer.
  - No physical cash is handled directly by ERP software.
- **Unresolved Business Decision**:
  - What is the formal internal control policy for verifying deposits? (Single treasurer verification vs dual treasurer + auditor review).
  - What is the dispute window for unreferenced, misidentified, or disputed deposits?
  - What happens if bank statements reflect deposits that no member has claimed after X months?
- **Proposed Technical Safeguard (v1 Software)**:
  - Contributions are created in a provisional `RECORDED` status.
  - A contribution cannot be marked `VERIFIED` without explicit entry of a unique `bank_reference` and the recording of the verifying user's ID.
  - Corrections are never performed via UPDATE; they require explicit REVERSAL transactions.
  - Unidentified bank inflows cannot be assigned to member accounts without positive documentation.

---

### 4.3 Reserve Fund Necessity & Rental Income Allocation (UBR-18)
- **Confirmed Cooperative Requirement**:
  - Investment property and rental project earnings belong exclusively to the cooperative union, not to individual members.
  - Cooperative income supports normal union operating expenses.
  - The remaining rental-project income is designated for the mall project.
  - No investment or rental profits are distributed as member dividends.
- **Unresolved Business Decision**:
  - Is a formal statutory "Reserve Fund" required under the cooperative's governing legal framework or union bylaws?
  - What is the exact percentage or priority formula for allocating gross rental income between:
    1. Union operating expenses.
    2. Property maintenance and operational costs.
    3. Mall project construction capital.
    4. Statutory reserve (if required).
- **Proposed Technical Safeguard (v1 Software)**:
  - `FundType` includes `OPERATING`, `PROJECT`, `RENTAL_INCOME`, and a configurable `RESERVE` account placeholder.
  - The software does **not** hardcode an automatic percentage split for rental income.
  - All rental revenues credit `coop.funds (RENTAL_INCOME)` and require explicit, auditable `FundTransfer` transactions to move capital into `OPERATING` or `PROJECT` accounts.

---

### 4.4 Relationship Between Existing Share Capital (ETB 60,000) and Recurring Contributions (ETB 300) (UBR-14)
- **Confirmed Cooperative Requirement**:
  - Each of the ~150 founding members currently holds 12 shares representing an initial share capital balance of ETB 60,000 (nominal ETB 5,000 per share).
  - Members make recurring contributions of ETB 300 (member/project) and ETB 50 (operating).
- **Unresolved Business Decision**:
  - What is the accounting relationship between the existing ETB 60,000 share balance and subsequent ETB 300 contributions?
  - Are they pooled into a single consolidated "Member Equity" ledger balance, or must they remain permanently distinct accounting tiers?
  - Upon member exit, are shares refunded under the same conditions as monthly contributions, or does share capital follow separate liquidation rules?
- **Proposed Technical Safeguard (v1 Software)**:
  - The database maintains `coop.shares` and `coop.contributions` as separate relational tables and ledger transaction streams.
  - The software strictly refrains from implementing opening-balance imports, automated balance merging, or unified member equity calculation algorithms until the cooperative assembly formally resolves this relationship.

---

## 5. Implementation Blocking Matrix

The following unresolved business decisions must be formally decided before implementing the corresponding downstream functional modules:

| Unresolved Decision | Blocked Chapter / Workflow | Why It Blocks Implementation |
|---|---|---|
| **UBR-14** (Share Capital vs Contribution Balance Relationship) | Chapter 04 (Member Balances) & Chapter 05 (Exit Payouts) | Cannot write balance calculation queries or exit settlement calculations without knowing if share capital and contributions combine. |
| **UBR-15** (Opening Balance Import Cut-Off & Format) | Chapter 05 (Financial Ledger) | Cannot seed or import opening ledger transactions for ~150 members without an approved cut-off date and transaction format. |
| **UBR-1** (Exit Payout Formula & Waiting Period) | Chapter 05 (Withdrawal Service - Exit Payouts) | Cannot implement automated withdrawal settlement for exiting members without an approved payout formula. |
| **UBR-8** (Partial Withdrawal Policy) | Chapter 05 (Withdrawal Service - Partial Withdrawals) | Workflow remains disabled behind feature flag until cooperative decides if partial withdrawals are allowed. |
| **UBR-9 & UBR-16** (Bank Verification & Inflow Protocol) | Chapter 05 (Contribution Verification Service) | Verification workflow remains manual single-step until cooperative defines formal multi-party sign-off requirements. |
| **UBR-18** (Rental Income Allocation & Reserve Mandate) | Chapter 06 (Assets & Rental Income) | Cannot automate rental-to-project fund transfers without an approved allocation formula. |
