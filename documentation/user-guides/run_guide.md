# run_guide.md - FinVault Quick Start & Run Guide

This guide walks you through launching the FinVault platform and performing manual verification of all features.

---

## 1. Quick Start Platform Launch

To run the entire platform (FastAPI backend + .NET Core frontend + Browser launch), simply execute the startup runner at the root of the workspace:

```cmd
run_platform.bat
```

This runner will automatically perform the following operations:
1. Opens a new terminal window starting the **FastAPI Backend (Uvicorn)** on port `8000`.
2. Initialises the **Qdrant Vector Index** and ingests documentation.
3. Opens a second terminal window starting the **ASP.NET Core Razor Pages Frontend** on port `5254`.
4. Opens your default web browser and navigates to the FinVault portal at `http://localhost:5254`.

*Keep both terminal windows running during development.*

---

## 2. Dynamic Student Switching

By default, the platform loads the profile of **Arjun Shah** (B.Tech CSE, currency: `INR`). 

* **To toggle profiles**: In the top-right corner of the topbar, use the **Mock Student** dropdown selector.
* **Sarah Connor**: Switch to **Sarah Connor** (M.Sc Data Science, currency: `USD`).
* **Visual Updates**: The system will automatically adapt the entire portal:
  * Profile avatar in the sidebar updates (`AS` vs `SC`).
  * Ledger values, receipts, and invoices display correct formatting (e.g. `$ 51,500.00` USD for Sarah and `₹ 0.00` for Arjun).
  * The refund filing input prefix dynamically changes (`$` vs `₹`) and safety warning/Director escalation threshold bounds are automatically adjusted.

---

## 3. Direct Ledger Payments

When a student has a remaining unpaid balance, they can pay off the amount directly through the portal:

1. Click on the **Payments** tab in the sidebar.
2. Under the invoices table, locate the pending invoice and click the **Pay Now** button.
3. Confirm the mock payment gateway checkout dialogue.
4. If a transaction exception already exists (such as a Razorpay mismatch), the system will trigger the automated Reconciliation Agent.
5. If no mismatch exists, it will execute a direct POST payment to the backend `/api/transactions/pay`, record the transaction, update the ledger, and clear the outstanding balance in real time.

---

## 4. Educational Loan Letters & Certified PDF Download

Students can request certified tuition fee estimate letters for bank educational loan applications:

1. Click on the **Loan Letters** tab in the sidebar.
2. Select a target bank (e.g. SBI, HDFC) and click **Request Certified Demand Letter**.
3. Once generated, click the **PDF** download button.
4. The backend dynamically compiles a certified demand letter in PDF format in-memory using `reportlab`. It draws correct student records, billing data, registrar digital signatures, and green compliance verification stamps, downloading the document cleanly.

---

## 5. Running Automated Integration Tests

To execute the automated integration test suite checking the API gateway, run:

```powershell
python testing/test_platform.py
```

This verifies that student lookup, payment endpoints, and certified PDF letters are executing correctly under standard runtime environments.
