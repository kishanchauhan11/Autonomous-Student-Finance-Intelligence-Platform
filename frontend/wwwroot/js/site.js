// API Gateway Endpoint Config
const API_BASE = "http://localhost:8000";

// Global State
let currentPortalMode = "student"; // student | admin
let currentStudentId = "STU-2021-4892"; // Mock authenticated student ID
let currentCurrency = "INR";
let activeTab = "dashboard";
let chatHistory = [];
let sidebarCollapsed = false;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    // Start by loading active student profile
    changeStudentProfile(currentStudentId);
    
    // Auto-refresh Kafka logs / approvals every 8 seconds if in admin view
    setInterval(() => {
        if (currentPortalMode === "admin" && (activeTab === "audit" || activeTab === "approvals")) {
            loadPortalData();
        }
    }, 8000);
});

// Helper to format currency dynamically based on active student
function formatCurrency(amount) {
    if (currentCurrency === "USD") {
        return `$ ${amount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    } else {
        return `₹ ${amount.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }
}

// Change Student Profile from dropdown
async function changeStudentProfile(studentId) {
    currentStudentId = studentId;
    try {
        const response = await fetch(`${API_BASE}/api/student/${studentId}`);
        if (!response.ok) throw new Error("Student load failed");
        const data = await response.json();
        const stud = data.student;
        
        // Update currency state
        currentCurrency = stud.currency || "INR";
        
        // Update UI prefix for refund amount input
        const currencyPrefix = document.querySelector(".input-currency-prefix");
        if (currencyPrefix) {
            currencyPrefix.innerText = currentCurrency === "USD" ? "$" : "₹";
        }
        
        // Update refund helper text
        const formHelper = document.querySelector(".form-helper");
        if (formHelper) {
            if (currentCurrency === "USD") {
                formHelper.innerText = "Requests exceeding $ 1,000.00 trigger manual Director verification.";
            } else {
                formHelper.innerText = "Requests exceeding ₹ 1,00,000.00 trigger manual Director verification.";
            }
        }
        
        // Update sidebar profile if in student mode
        const userAvatar = document.getElementById("user-avatar");
        const userName = document.getElementById("user-name");
        const userRole = document.getElementById("user-role");
        
        if (userAvatar && userName && userRole && currentPortalMode === "student") {
            const initials = stud.name.split(" ").map(n => n[0]).join("");
            userAvatar.innerText = initials;
            userName.innerText = stud.name;
            userRole.innerText = "Student";
        }
        
        // Force reload of active view data
        loadPortalData();
        
    } catch (e) {
        console.error(e);
        showToast("Error", "Could not switch student profile.", "error");
    }
}

// Portal Toggle (Student Portal <-> Accounts Office Portal)
function togglePortalMode() {
    const btn = document.getElementById("btn-toggle-portal");
    const sidebarStudent = document.getElementById("sidebar-student-section");
    const sidebarAdmin = document.getElementById("sidebar-admin-section");
    const userAvatar = document.getElementById("user-avatar");
    const userName = document.getElementById("user-name");
    const userRole = document.getElementById("user-role");
    const switcherWrapper = document.getElementById("student-switcher-wrapper");
    
    if (currentPortalMode === "student") {
        currentPortalMode = "admin";
        btn.innerText = "Switch to Student Portal";
        sidebarStudent.style.display = "none";
        sidebarAdmin.style.display = "block";
        if (switcherWrapper) switcherWrapper.style.display = "none";
        
        // Change user profile in sidebar to Finance Officer
        userAvatar.innerText = "FO";
        userName.innerText = "Sarah Jenkins";
        userRole.innerText = "Finance Officer";
        
        showToast("Access Granted", "Role changed to Accounts Finance Officer (Keycloak Session updated).", "success");
        switchTab("reconciliation");
    } else {
        currentPortalMode = "student";
        btn.innerText = "Switch to Accounts Portal";
        sidebarStudent.style.display = "block";
        sidebarAdmin.style.display = "none";
        if (switcherWrapper) switcherWrapper.style.display = "flex";
        
        // Reset to active Student
        const dropdown = document.getElementById("student-switcher");
        if (dropdown) {
            dropdown.value = currentStudentId;
        }
        
        // Fetch current active student profile to update sidebar and reload data
        changeStudentProfile(currentStudentId);
        
        showToast("Access Restored", "Returned to Student Portal view.", "info");
        switchTab("dashboard");
    }
}

// Sidebar toggle collapse
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebarCollapsed = !sidebarCollapsed;
    if (sidebarCollapsed) {
        sidebar.style.width = "64px";
        document.querySelectorAll(".sidebar-user-info, .sidebar-subtitle, .sidebar-section-title, .sidebar-logo").forEach(el => el.style.display = "none");
    } else {
        sidebar.style.width = "240px";
        document.querySelector(".sidebar-subtitle").style.display = "block";
        document.querySelector(".sidebar-logo").style.display = "block";
        if (currentPortalMode === "student") {
            document.getElementById("sidebar-student-section").querySelectorAll(".sidebar-section-title").forEach(el => el.style.display = "block");
        } else {
            document.getElementById("sidebar-admin-section").querySelectorAll(".sidebar-section-title").forEach(el => el.style.display = "block");
        }
        document.querySelector(".sidebar-user-info").style.display = "flex";
    }
}

// Switch between dashboard tabs
function switchTab(tabName) {
    activeTab = tabName;
    
    // Deactivate all sidebar links
    document.querySelectorAll(".sidebar-item").forEach(item => {
        item.classList.remove("active");
    });
    
    // Hide all view content wrappers
    document.querySelectorAll(".view-content").forEach(view => {
        view.style.display = "none";
    });
    
    // Activate clicked item and corresponding view
    const viewId = `view-${tabName}`;
    const viewElement = document.getElementById(viewId);
    if (viewElement) {
        viewElement.style.display = "block";
    }
    
    // Find active link
    const links = document.querySelectorAll(".sidebar-item");
    links.forEach(link => {
        if (link.getAttribute("onclick").includes(`'${tabName}'`)) {
            link.classList.add("active");
        }
    });
    
    // Update breadcrumb
    const breadcrumb = document.getElementById("breadcrumb");
    const cleanName = tabName.charAt(0).toUpperCase() + tabName.slice(1).replace("-", " ");
    breadcrumb.innerText = `Portal / ${currentPortalMode === "student" ? "Student" : "Admin"} ${cleanName}`;
    
    loadPortalData();
}

// Master portal data dispatcher
function loadPortalData() {
    if (activeTab === "dashboard") {
        fetchStudentDashboard();
    } else if (activeTab === "payments") {
        fetchFeePayments();
    } else if (activeTab === "refunds") {
        fetchRefundTracker();
    } else if (activeTab === "loans") {
        fetchLoanLetters();
    } else if (activeTab === "reconciliation") {
        fetchReconciliationExceptions();
    } else if (activeTab === "approvals") {
        fetchApprovalsQueue();
    } else if (activeTab === "audit") {
        fetchAuditLogs();
    }
}

// ── STUDENT VIEW FETCHERS ───────────────────────────────────

// Fetch student data & ledger
async function fetchStudentDashboard() {
    try {
        const response = await fetch(`${API_BASE}/api/student/${currentStudentId}`);
        if (!response.ok) throw new Error("Student data load failed");
        
        const data = await response.json();
        const stud = data.student;
        const ledger = data.ledger;
        
        // Update header info
        document.getElementById("student-profile-program").innerText = `${stud.program}  ·  Student ID: ${stud.id}  ·  Sem ${stud.semester}`;
        
        // Populate KPI cards (right-aligned currency)
        document.getElementById("kpi-fees-due").innerHTML = formatCurrency(ledger.balance);
        document.getElementById("kpi-fees-paid").innerHTML = formatCurrency(ledger.paid);
        document.getElementById("kpi-scholarship").innerHTML = formatCurrency(ledger.scholarship);
        
        // Check if there are active refunds to display in KPI
        const refResp = await fetch(`${API_BASE}/api/refunds/${currentStudentId}`);
        const refunds = await refResp.json();
        let pendingRefundAmt = 0;
        refunds.forEach(r => {
            if (r.stage !== "CREDITED" && r.stage !== "REJECTED") {
                pendingRefundAmt += r.amount;
            }
        });
        document.getElementById("kpi-refund-pending").innerHTML = formatCurrency(pendingRefundAmt);
        
        // Update payment deadlines card balance
        document.getElementById("deadlines-balance").innerHTML = formatCurrency(ledger.balance);
        
        // Update recent transactions list (max 5)
        const txnResp = await fetch(`${API_BASE}/api/transactions/${currentStudentId}`);
        const txns = await txnResp.json();
        const tbody = document.getElementById("dashboard-txns-body");
        tbody.innerHTML = "";
        
        if (txns.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #999999;">No transaction history found.</td></tr>`;
        } else {
            txns.slice(0, 5).forEach(t => {
                tbody.innerHTML += `
                    <tr>
                        <td class="mono font-semibold">${t.txn_id}</td>
                        <td>${t.date}</td>
                        <td>${t.category}</td>
                        <td class="currency-cell mono">${formatCurrency(t.amount)}</td>
                        <td><span class="badge cleared">${t.status}</span></td>
                    </tr>
                `;
            });
        }
    } catch (e) {
        console.error(e);
        showToast("Error", "Could not connect to FastAPI server. Ensure python backend is running on port 8000.", "error");
    }
}

// Fetch invoices and payments
async function fetchFeePayments() {
    try {
        const studentResp = await fetch(`${API_BASE}/api/student/${currentStudentId}`);
        const studData = await studentResp.json();
        const ledger = studData.ledger;
        
        // Populate summary values
        document.getElementById("pay-summary-billed").innerHTML = formatCurrency(ledger.billed);
        document.getElementById("pay-summary-paid").innerHTML = formatCurrency(ledger.paid);
        document.getElementById("pay-summary-due").innerHTML = formatCurrency(ledger.balance);
        
        // Populate invoice table
        const txnResp = await fetch(`${API_BASE}/api/transactions/${currentStudentId}`);
        const txns = await txnResp.json();
        const tbody = document.getElementById("payments-table-body");
        tbody.innerHTML = "";
        
        // Default Billed Invoice row
        const termName = currentStudentId === "STU-2021-4892" ? "Sem 7" : "Sem 3";
        tbody.innerHTML += `
            <tr class="${ledger.balance > 0 ? 'overdue' : ''}">
                <td class="mono">INV-2026-${currentStudentId === "STU-2021-4892" ? "7A" : "3A"}</td>
                <td>Tuition Fee ${studData.student.program} ${termName}</td>
                <td>15 May 2026</td>
                <td class="currency-cell mono">${formatCurrency(ledger.billed)}</td>
                <td class="currency-cell mono">${formatCurrency(ledger.paid)}</td>
                <td class="currency-cell mono font-semibold">${formatCurrency(ledger.balance)}</td>
                <td>
                    <span class="badge ${ledger.balance === 0 ? 'cleared' : 'pending'}">
                        ${ledger.balance === 0 ? 'CLEARED' : 'PENDING'}
                    </span>
                </td>
                <td class="actions-cell">
                    ${ledger.balance > 0 ? `<button class="btn btn-secondary btn-sm" onclick="payOutstandingAmount(${ledger.balance})">Pay Now</button>` : `<button class="btn btn-ghost btn-sm" onclick="alert('Paid in full.')">Invoice</button>`}
                </td>
            </tr>
        `;
        
        // Historical receipts
        txns.forEach(t => {
            tbody.innerHTML += `
                <tr>
                    <td class="mono">${t.txn_id}</td>
                    <td>Receipt - ${t.category}</td>
                    <td>${t.date}</td>
                    <td class="currency-cell mono">${formatCurrency(t.amount)}</td>
                    <td class="currency-cell mono">${formatCurrency(t.amount)}</td>
                    <td class="currency-cell mono">${formatCurrency(0)}</td>
                    <td><span class="badge cleared">${t.status}</span></td>
                    <td class="actions-cell">
                        <button class="btn btn-ghost btn-sm" onclick="alert('Downloading Receipt PDF...')"><i class="ph-download-simple"></i> Receipt</button>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error(e);
    }
}

// Pay outstanding tuition mock action
async function payOutstandingAmount(amount) {
    if (confirm(`Authorize mock payment gateway checkout of ${formatCurrency(amount)}?`)) {
        try {
            // Trigger reconciliation or mock payment sync
            const res = await fetch(`${API_BASE}/api/reconcile/run/${currentStudentId}`, { method: 'POST' });
            const data = await res.json();
            
            if (data.reconciled) {
                showToast("Payment Successful", `Mock gateway verified. Ledger updated: ${formatCurrency(data.amount)}`, "success");
            } else {
                // Post payment transaction to backend
                const payRes = await fetch(`${API_BASE}/api/transactions/pay`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        student_id: currentStudentId,
                        amount: amount,
                        category: "Tuition Fee Sem " + (currentStudentId === "STU-2021-4892" ? "7" : "3"),
                        method: "Net Banking"
                    })
                });
                
                if (payRes.ok) {
                    showToast("Payment Successful", `Payment of ${formatCurrency(amount)} processed and ledger updated.`, "success");
                } else {
                    showToast("Payment Failed", "Mock payment processing failed.", "error");
                }
            }
            loadPortalData();
        } catch (e) {
            console.error(e);
            showToast("Payment Error", "An error occurred during payment processing.", "error");
        }
    }
}

// Fetch refund details & stepper
async function fetchRefundTracker() {
    try {
        const response = await fetch(`${API_BASE}/api/refunds/${currentStudentId}`);
        const refunds = await response.json();
        const tbody = document.getElementById("refunds-table-body");
        tbody.innerHTML = "";
        
        const stepperContainer = document.getElementById("active-refund-stepper-container");
        
        if (refunds.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #999999;">No refund requests logged.</td></tr>`;
            stepperContainer.innerHTML = `<div style="text-align: center; padding: 24px; color: #999999; font-style: italic;">No active refund pipeline to track. To request a refund, use the AI Assistant or fill the form below.</div>`;
        } else {
            const activeRefund = refunds[refunds.length - 1]; // Latest refund
            
            // Render horizontal stepper for the latest refund
            const stages = ["SUBMITTED", "VERIFICATION", "APPROVAL", "PROCESSING", "CREDITED"];
            let activeIdx = stages.indexOf(activeRefund.stage);
            if (activeRefund.stage === "REJECTED") activeIdx = 2; // For visual placement
            
            let nodesHtml = "";
            stages.forEach((stage, idx) => {
                let statusClass = "";
                if (idx < activeIdx) statusClass = "completed";
                else if (idx === activeIdx) {
                    statusClass = activeRefund.stage === "REJECTED" ? "active rejected" : "active";
                }
                
                nodesHtml += `
                    <div class="step-node ${statusClass}">
                        <div class="step-circle">${idx + 1}</div>
                        <div class="step-label">${stage}</div>
                        <div class="step-line"></div>
                    </div>
                `;
            });
            
            stepperContainer.innerHTML = `
                <div style="font-weight: 600; margin-bottom: 20px; font-size: 14px; text-transform: uppercase;">
                    Request Pipeline: ${activeRefund.request_id} — Amount: ${formatCurrency(activeRefund.amount)}
                </div>
                <div class="stepper">${nodesHtml}</div>
                <div style="font-size: 12px; color: #6B6B6B; margin-top: 16px; text-align: center;">
                    ${activeRefund.stage === "VERIFICATION" ? "⏱ Verification: accounts department is validating proof documents. SLA 1-3 days." : ""}
                    ${activeRefund.stage === "APPROVAL" ? "⏱ Accounts Approval: waiting for Finance Officer final authorization." : ""}
                    ${activeRefund.stage === "PROCESSING" ? "🔄 ERP Processing: sync queue released, bank routing initiated." : ""}
                    ${activeRefund.stage === "CREDITED" ? "✓ Credited: funds released and cleared by clearing house bank." : ""}
                </div>
            `;
            
            // List all refunds
            refunds.forEach(r => {
                tbody.innerHTML += `
                    <tr>
                        <td class="mono font-semibold">${r.request_id}</td>
                        <td>${r.description}</td>
                        <td>${r.submitted_date}</td>
                        <td class="currency-cell mono">${formatCurrency(r.amount)}</td>
                        <td><span class="badge ${r.stage.toLowerCase()}">${r.stage}</span></td>
                        <td class="mono">${r.eta_days} Days</td>
                    </tr>
                `;
            });
        }
    } catch (e) {
        console.error(e);
    }
}

// Log new refund request
async function fileNewRefund(event) {
    event.preventDefault();
    const amount = parseFloat(document.getElementById("refund-form-amount").value);
    const desc = document.getElementById("refund-form-desc").value;
    
    if (isNaN(amount) || amount <= 0) {
        alert("Please enter a valid amount.");
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/refunds/request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: currentStudentId, amount: amount, description: desc })
        });
        
        if (res.ok) {
            showToast("Refund Request Logged", `Request processed by Refund Agent. Tracking ID generated.`, "success");
            document.getElementById("refund-creation-form").reset();
            fetchRefundTracker();
            // Toggle sidebar badge / count if needed
        }
    } catch (e) {
        console.error(e);
    }
}

// Fetch education loan demand letters
async function fetchLoanLetters() {
    try {
        const response = await fetch(`${API_BASE}/api/loans/${currentStudentId}`);
        const letters = await response.json();
        const tbody = document.getElementById("loans-table-body");
        tbody.innerHTML = "";
        
        if (letters.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #999999;">No education loan demand letters requested.</td></tr>`;
        } else {
            letters.forEach(l => {
                tbody.innerHTML += `
                    <tr>
                        <td class="mono font-semibold">${l.letter_id}</td>
                        <td>${l.program}</td>
                        <td>${l.bank}</td>
                        <td class="currency-cell mono">${formatCurrency(l.amount)}</td>
                        <td><span class="badge cleared">${l.status}</span></td>
                        <td>
                            <a href="${API_BASE}${l.download_url}" target="_blank" class="btn btn-secondary btn-sm" style="padding: 2px 8px; height: 26px;">
                                <i class="ph-download-simple"></i> PDF
                            </a>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (e) {
        console.error(e);
    }
}

// Request new education loan letter
async function requestLoanLetter(event) {
    event.preventDefault();
    const bank = document.getElementById("loan-form-bank").value;
    const term = document.getElementById("loan-form-term").value;
    
    try {
        // Fetch current billed amount
        const studResp = await fetch(`${API_BASE}/api/student/${currentStudentId}`);
        const studData = await studResp.json();
        const billed = studData.ledger.billed;
        
        const res = await fetch(`${API_BASE}/api/loans/request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: currentStudentId, program: studData.student.program, bank: bank, amount: billed })
        });
        
        if (res.ok) {
            showToast("Letter Generated", `Loan demand letter for ${bank} generated with digital signature.`, "success");
            document.getElementById("loan-creation-form").reset();
            fetchLoanLetters();
        }
    } catch (e) {
        console.error(e);
    }
}


// ── ADMIN / ACCOUNTS OFFICER VIEW FETCHERS ───────────────────

// Fetch reconciliation mismatch exceptions
async function fetchReconciliationExceptions() {
    try {
        const response = await fetch(`${API_BASE}/api/exceptions`);
        const exceptions = await response.json();
        const tbody = document.getElementById("reconciliation-table-body");
        tbody.innerHTML = "";
        
        let exceptionsCount = 0;
        exceptions.forEach(exc => {
            if (exc.status === "UNMATCHED") exceptionsCount++;
            
            tbody.innerHTML += `
                <tr class="${exc.status === 'UNMATCHED' ? 'overdue' : ''}">
                    <td class="mono font-semibold">${exc.exception_id}</td>
                    <td class="mono">${exc.txn_id}</td>
                    <td>${exc.student_id}</td>
                    <td class="currency-cell mono">₹ ${exc.expected.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                    <td class="currency-cell mono">₹ ${exc.received.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                    <td class="currency-cell mono font-semibold" style="font-style: italic;">
                        ${exc.delta < 0 ? '−' : ''} ₹ ${Math.abs(exc.delta).toLocaleString('en-IN', {minimumFractionDigits: 2})}
                    </td>
                    <td>${exc.source}</td>
                    <td>
                        <span class="badge ${exc.status === 'UNMATCHED' ? 'pending' : 'cleared'}">
                            ${exc.status}
                        </span>
                    </td>
                    <td class="actions-cell">
                        ${exc.status === 'UNMATCHED' ? `<button class="btn btn-secondary btn-sm" onclick="reconcileException('${exc.student_id}')">Sync ERP</button>` : `<span style="font-size: 11px; color:#999999;">Resolved</span>`}
                    </td>
                </tr>
            `;
        });
        
        document.getElementById("kpi-exceptions").innerHTML = exceptionsCount;
        document.getElementById("kpi-exceptions-card").style.borderLeftColor = exceptionsCount > 0 ? "#0A0A0A" : "#D0D0D0";
    } catch (e) {
        console.error(e);
    }
}

// Trigger single exception reconciliation
async function reconcileException(studentId) {
    try {
        const res = await fetch(`${API_BASE}/api/reconcile/run/${studentId}`, { method: 'POST' });
        const data = await res.json();
        if (data.reconciled) {
            showToast("ERP Reconciled", `Transaction ${data.transaction_id} matching delta synchronized successfully.`, "success");
            fetchReconciliationExceptions();
        }
    } catch (e) {
        console.error(e);
    }
}

// Fetch pending officer approvals
async function fetchApprovalsQueue() {
    try {
        const response = await fetch(`${API_BASE}/api/approvals`);
        const approvals = await response.json();
        const tbody = document.getElementById("approvals-table-body");
        tbody.innerHTML = "";
        
        let pendingCount = 0;
        approvals.forEach(app => {
            if (app.status === "PENDING") pendingCount++;
            
            tbody.innerHTML += `
                <tr class="${app.status === 'PENDING' ? 'selected' : ''}">
                    <td class="mono font-semibold">${app.approval_id}</td>
                    <td><strong>${app.type}</strong></td>
                    <td>${app.student_id}</td>
                    <td class="currency-cell mono">₹ ${app.amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                    <td>
                        <span class="badge ${app.priority === 'HIGH' ? 'approved' : 'pending'}">
                            ${app.priority}
                        </span>
                    </td>
                    <td class="mono ${app.age_hours > 24 ? 'font-semibold italic' : ''}">${app.age_hours} Hours</td>
                    <td>
                        <span class="badge ${app.status.toLowerCase()}">${app.status}</span>
                    </td>
                    <td class="actions-cell">
                        ${app.status === 'PENDING' ? `
                            <button class="btn btn-primary btn-sm" onclick="processApproval('${app.approval_id}', 'APPROVE')">Approve</button>
                            <button class="btn btn-secondary btn-sm" onclick="processApproval('${app.approval_id}', 'REJECT')">Reject</button>
                        ` : `Processed`}
                    </td>
                </tr>
            `;
        });
        
        document.getElementById("notif-count").innerText = pendingCount;
    } catch (e) {
        console.error(e);
    }
}

// Process pending approval task
async function processApproval(approvalId, action) {
    try {
        const res = await fetch(`${API_BASE}/api/approvals/${approvalId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, officer: "Sarah Jenkins" })
        });
        
        if (res.ok) {
            showToast("Approval Logged", `Task ${approvalId} has been successfully ${action}D.`, "success");
            fetchApprovalsQueue();
        }
    } catch (e) {
        console.error(e);
    }
}

// Format Kafka payload for human-readable display in the broker log
function formatKafkaPayload(topic, payload) {
    if (!payload || typeof payload !== 'object') return String(payload);
    
    try {
        // For agent-response-generated: show key fields, truncate long response text
        if (topic === 'agent-response-generated') {
            const response = payload.response || '';
            const truncated = response.replace(/#+\s*/g, '').replace(/\*+/g, '').replace(/`/g, '').trim();
            const shortResp = truncated.length > 80 ? truncated.substring(0, 80) + '...' : truncated;
            return `<strong>Student:</strong> ${payload.student_id || '—'} &nbsp;|&nbsp; <strong>Intent:</strong> ${payload.intent || '—'} &nbsp;|&nbsp; <strong>Query:</strong> "${(payload.query || '').substring(0, 40)}" &nbsp;|&nbsp; <em style="color:#555;">${shortResp}</em>`;
        }
        
        // For payment-reconciled: show transaction summary
        if (topic === 'payment-reconciled') {
            return `<strong>TXN:</strong> ${payload.txn_id || '—'} &nbsp;|&nbsp; <strong>Student:</strong> ${payload.student_id || '—'} &nbsp;|&nbsp; <strong>Amount:</strong> ${payload.amount != null ? payload.amount.toLocaleString() : '—'} &nbsp;|&nbsp; <strong>Status:</strong> ${payload.status || '—'} &nbsp;|&nbsp; <strong>Method:</strong> ${payload.method || '—'}`;
        }
        
        // For refund-submitted: show refund summary
        if (topic === 'refund-submitted') {
            return `<strong>Refund ID:</strong> ${payload.request_id || '—'} &nbsp;|&nbsp; <strong>Student:</strong> ${payload.student_id || '—'} &nbsp;|&nbsp; <strong>Amount:</strong> ${payload.amount != null ? payload.amount.toLocaleString() : '—'} &nbsp;|&nbsp; <strong>Stage:</strong> ${payload.stage || '—'}`;
        }
        
        // For notification-sent:
        if (topic === 'notification-sent') {
            const msg = (payload.message || '').substring(0, 80);
            return `<strong>Student:</strong> ${payload.student_id || '—'} &nbsp;|&nbsp; <strong>Channel:</strong> ${payload.channel || '—'} &nbsp;|&nbsp; <em>${msg}</em>`;
        }
        
        // For approval-required / escalation-triggered:
        if (topic === 'approval-required' || topic === 'escalation-triggered') {
            return `<strong>Approval:</strong> ${payload.approval_id || payload.type || '—'} &nbsp;|&nbsp; <strong>Student:</strong> ${payload.student_id || '—'} &nbsp;|&nbsp; <strong>Priority:</strong> ${payload.priority || '—'} &nbsp;|&nbsp; <strong>Status:</strong> ${payload.status || '—'}`;
        }
        
        // For officer-ai-query
        if (topic === 'officer-ai-query') {
            const preview = (payload.response_preview || '').substring(0, 80);
            return `<strong>Officer:</strong> ${payload.officer_id || '—'} &nbsp;|&nbsp; <strong>Query:</strong> "${(payload.query || '').substring(0, 50)}" &nbsp;|&nbsp; <em style="color:#555;">${preview}</em>`;
        }
        
        // Generic: show top-level keys in a readable way
        const parts = Object.entries(payload)
            .filter(([k, v]) => typeof v !== 'object' && String(v).length < 60)
            .map(([k, v]) => `<strong>${k}:</strong> ${String(v).substring(0, 50)}`)
            .slice(0, 5)
            .join(' &nbsp;|&nbsp; ');
        return parts || JSON.stringify(payload).substring(0, 120);
    } catch(e) {
        return JSON.stringify(payload).substring(0, 120);
    }
}

// Fetch Kafka logs and compliance events
async function fetchAuditLogs() {
    try {
        const response = await fetch(`${API_BASE}/api/kafka/events`);
        const events = await response.json();
        const tbody = document.getElementById("audit-table-body");
        tbody.innerHTML = "";
        
        if (events.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color:#999999; font-style:italic;">No events in Kafka broker logs yet. Interacting with student services will publish events.</td></tr>`;
        } else {
            // Display latest first
            events.slice().reverse().forEach(ev => {
                const dateStr = new Date(ev.timestamp).toLocaleTimeString();
                const formattedPayload = formatKafkaPayload(ev.topic, ev.payload);
                tbody.innerHTML += `
                    <tr>
                        <td class="mono" style="font-size:11px; white-space: nowrap;">${dateStr}</td>
                        <td><span class="badge processing" style="border-radius:12px; border-width:1px; text-transform:uppercase;">${ev.topic}</span></td>
                        <td style="font-size:11.5px; line-height: 1.6; padding: 8px 12px;">${formattedPayload}</td>
                        <td><span class="badge cleared" style="font-size:9px;">SECURE</span></td>
                    </tr>
                `;
            });
        }
    } catch (e) {
        console.error(e);
    }
}

// ── TOAST HELPER ───────────────────────────────────────────
function showToast(title, description, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast`;
    
    let iconClass = "ph-info";
    if (type === "success") {
        iconClass = "ph-check-circle";
        toast.style.borderLeftColor = "#0A0A0A";
    } else if (type === "warning") {
        iconClass = "ph-warning-circle";
        toast.style.borderLeftColor = "#0A0A0A";
    } else if (type === "error") {
        iconClass = "ph-x-circle";
        toast.style.borderWidth = "2px";
        toast.style.borderColor = "#0A0A0A";
    }
    
    toast.innerHTML = `
        <i class="${iconClass} toast-icon"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-description">${description}</div>
        </div>
        <i class="ph-x toast-close" onclick="this.parentElement.remove()"></i>
    `;
    
    container.appendChild(toast);
    
    // Trigger entry transition
    setTimeout(() => {
        toast.classList.add("show");
    }, 10);
    
    // Auto remove after 5s unless error
    if (type !== "error") {
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 250);
        }, 5000);
    }
}

// ── AI ASSISTANT CHAT HANDLERS ─────────────────────────────
function toggleChatPanel() {
    // Route to correct chat panel based on current portal mode
    if (currentPortalMode === "admin") {
        const officerPanel = document.getElementById("officer-ai-panel");
        if (officerPanel) officerPanel.classList.toggle("open");
        // Close student panel if open
        const studentPanel = document.getElementById("ai-panel");
        if (studentPanel) studentPanel.classList.remove("open");
    } else {
        const panel = document.getElementById("ai-panel");
        if (panel) panel.classList.toggle("open");
        // Close officer panel if open
        const officerPanel = document.getElementById("officer-ai-panel");
        if (officerPanel) officerPanel.classList.remove("open");
    }
}

function toggleOfficerChatPanel() {
    const panel = document.getElementById("officer-ai-panel");
    if (panel) panel.classList.toggle("open");
    // Close student chat if open
    const studentPanel = document.getElementById("ai-panel");
    if (studentPanel) studentPanel.classList.remove("open");
}

function toggleNotifications() {
    showToast("Notifications Center", "No new alerts. Keycloak session active.", "info");
}

function handleChatKey(event) {
    if (event.key === "Enter") {
        sendChatMessage();
    }
}

function handleOfficerChatKey(event) {
    if (event.key === "Enter") {
        sendOfficerChatMessage();
    }
}

// ── OFFICER AI CHAT ─────────────────────────────────────────
let officerChatHistory = [];

async function sendOfficerChatMessage() {
    const input = document.getElementById("officer-ai-chat-input");
    const text = input.value.trim();
    if (!text) return;
    
    input.value = "";
    
    const thread = document.getElementById("officer-ai-chat-thread");
    
    // Render Officer Message Bubble
    const userContainer = document.createElement("div");
    userContainer.className = "chat-bubble-container user";
    userContainer.innerHTML = `
        <div class="chat-bubble">${text}</div>
        <div class="chat-timestamp">Just now</div>
    `;
    thread.appendChild(userContainer);
    thread.scrollTop = thread.scrollHeight;
    
    officerChatHistory.push({ role: "user", content: text });
    
    // Typing indicator
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.id = "officer-chat-typing";
    typing.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
    thread.appendChild(typing);
    thread.scrollTop = thread.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE}/api/officer/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                officer_id: "FO-SARAH-001",
                message: text,
                history: officerChatHistory.slice(-10)
            })
        });
        
        document.getElementById("officer-chat-typing")?.remove();
        
        if (!response.ok) throw new Error("Officer agent error");
        const data = await response.json();
        
        const aiContainer = document.createElement("div");
        aiContainer.className = "chat-bubble-container ai";
        
        let formattedRes = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response;
        aiContainer.innerHTML = `
            <div class="chat-bubble">
                ${formattedRes}
                <div class="chat-tag-verified">Finance Officer Intelligence Core | Admin Mode: SECURE</div>
            </div>
            <div class="chat-timestamp">Just now</div>
        `;
        thread.appendChild(aiContainer);
        thread.scrollTop = thread.scrollHeight;
        
        officerChatHistory.push({ role: "assistant", content: data.response });
        
        // Refresh admin data if relevant
        if (/refund|approval|reconcil|exception|student|balance/i.test(text)) {
            loadPortalData();
        }
    } catch(e) {
        console.error(e);
        document.getElementById("officer-chat-typing")?.remove();
        const errContainer = document.createElement("div");
        errContainer.className = "chat-bubble-container ai";
        errContainer.innerHTML = `
            <div class="chat-bubble" style="border: 2px solid #0A0A0A; font-weight: bold;">
                ✕ Officer AI Unavailable: Could not connect to the officer agent gateway.
            </div>
            <div class="chat-timestamp">Just now</div>
        `;
        thread.appendChild(errContainer);
        thread.scrollTop = thread.scrollHeight;
    }
}

// ── STUDENT AI CHAT ─────────────────────────────────────────
async function sendChatMessage() {
    const input = document.getElementById("ai-chat-input");
    const text = input.value.trim();
    if (!text) return;
    
    input.value = "";
    
    const thread = document.getElementById("ai-chat-thread");
    
    // 1. Render User Bubble
    const userContainer = document.createElement("div");
    userContainer.className = "chat-bubble-container user";
    userContainer.innerHTML = `
        <div class="chat-bubble">${text}</div>
        <div class="chat-timestamp">Just now</div>
    `;
    thread.appendChild(userContainer);
    thread.scrollTop = thread.scrollHeight;
    
    // PUSH user message to local history
    chatHistory.push({ role: "user", content: text });
    
    // 2. Render Typing Indicator
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.id = "chat-typing";
    typing.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    thread.appendChild(typing);
    thread.scrollTop = thread.scrollHeight;
    
    try {
        // 3. POST to FastAPI Chat
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: currentStudentId,
                message: text,
                history: chatHistory.slice(-10) // Send last 10 messages context
            })
        });
        
        // Remove typing indicator
        document.getElementById("chat-typing").remove();
        
        if (!response.ok) throw new Error("Agent orchestrator error");
        
        const data = await response.json();
        
        // Render AI Bubble
        const aiContainer = document.createElement("div");
        aiContainer.className = "chat-bubble-container ai";
        
        // Check if there are citations (RAG context matched)
        let citationsHtml = "";
        if (data.context) {
            citationsHtml = `
                <div class="chat-citation-list">
                    <span class="chat-citation-chip"><i class="ph-file-text"></i> Finance Policy</span>
                </div>
            `;
        }
        
        // Format response using Marked.js
        let formattedRes = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response;
            
        aiContainer.innerHTML = `
            <div class="chat-bubble">
                ${formattedRes}
                ${citationsHtml}
                <div class="chat-tag-verified">Verified by Finance Intelligence AI Core | Policy Compliance: SECURE</div>
            </div>
            <div class="chat-timestamp">Just now</div>
        `;
        thread.appendChild(aiContainer);
        thread.scrollTop = thread.scrollHeight;
        
        // PUSH AI response to local history
        chatHistory.push({ role: "assistant", content: data.response });
        
        // Trigger page updates if the transaction occurred
        if (text.toLowerCase().includes("reconcil") || text.toLowerCase().includes("paid") || text.toLowerCase().includes("refund") || text.toLowerCase().includes("loan")) {
            loadPortalData();
        }
        
    } catch (e) {
        console.error(e);
        document.getElementById("chat-typing")?.remove();
        
        const errContainer = document.createElement("div");
        errContainer.className = "chat-bubble-container ai";
        errContainer.innerHTML = `
            <div class="chat-bubble" style="border: 2px solid #0A0A0A; font-weight: bold;">
                ✕ Connectivity Error: Could not connect to agent orchestrator gateway. Please ensure the backend is running.
            </div>
            <div class="chat-timestamp">Just now</div>
        `;
        thread.appendChild(errContainer);
        thread.scrollTop = thread.scrollHeight;
    }
}
