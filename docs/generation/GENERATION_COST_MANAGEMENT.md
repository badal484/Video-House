# Generation Cost & Budget Management
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation  
**Document:** GENERATION_COST_MANAGEMENT.md  
**Version:** 1.0.0  

---

## 1. Budget Tiers & Cost Controls

To prevent runaway API expenses during autonomous agent iterations, Department 15 enforces a multi-tier budget firewall:

```
[Global Studio Ceiling] ──> [Project Budget Cap ($100)] ──> [Per-Shot Budget Cap ($5.00)]
                                                                     │
                                                                     ▼
                                                         [High-Cost Gate (> $1.00)]
                                                         Requires User Click-to-Approve
```

---

## 2. Real-Time Tracking & Persistent Ledger

- Every generation job records `estimated_cost_usd` and `actual_cost_usd` in `generation_jobs`.
- Expenditures are aggregated per project in `generation_budgets`.
- If an operation would breach the remaining budget, the job transition is set to `JobStatus.BLOCKED` with detailed error diagnostics.
