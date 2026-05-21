-- =========================================================================
-- Autonomous Student Finance Intelligence Platform - MSSQL Schema Definition
-- =========================================================================

-- Create Students table
CREATE TABLE Students (
    id NVARCHAR(50) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    program NVARCHAR(100) NOT NULL,
    semester INT NOT NULL,
    email NVARCHAR(100) NOT NULL,
    phone NVARCHAR(30) NOT NULL,
    billed_amount DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    scholarship_amount DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    paid_amount DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    late_fees DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    currency NVARCHAR(10) NOT NULL DEFAULT 'INR'
);

-- Create Transactions table
CREATE TABLE Transactions (
    txn_id NVARCHAR(50) PRIMARY KEY,
    student_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Students(id),
    date NVARCHAR(50) NOT NULL,
    category NVARCHAR(100) NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    method NVARCHAR(50) NOT NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'PENDING'
);

-- Create Refunds table
CREATE TABLE Refunds (
    request_id NVARCHAR(50) PRIMARY KEY,
    student_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Students(id),
    description NVARCHAR(255) NOT NULL,
    submitted_date NVARCHAR(50) NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    stage NVARCHAR(30) NOT NULL DEFAULT 'SUBMITTED', -- SUBMITTED, VERIFICATION, APPROVAL, PROCESSING, CREDITED
    eta_days INT NOT NULL DEFAULT 15
);

-- Create RefundHistory table to track status transition audit trails
CREATE TABLE RefundHistory (
    id INT IDENTITY(1,1) PRIMARY KEY,
    request_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Refunds(request_id),
    status NVARCHAR(30) NOT NULL,
    date NVARCHAR(50) NOT NULL,
    action_by NVARCHAR(100) NOT NULL
);

-- Create LoanLetters table
CREATE TABLE LoanLetters (
    letter_id NVARCHAR(50) PRIMARY KEY,
    student_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Students(id),
    program NVARCHAR(100) NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    bank NVARCHAR(100) NOT NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'APPROVED',
    generated_on NVARCHAR(50) NOT NULL,
    download_url NVARCHAR(255) NOT NULL
);

-- Create ReconciliationExceptions table
CREATE TABLE ReconciliationExceptions (
    exception_id NVARCHAR(50) PRIMARY KEY,
    txn_id NVARCHAR(50) NOT NULL,
    student_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Students(id),
    expected DECIMAL(18, 2) NOT NULL,
    received DECIMAL(18, 2) NOT NULL,
    delta DECIMAL(18, 2) NOT NULL,
    source NVARCHAR(100) NOT NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'UNMATCHED', -- UNMATCHED, RECONCILED
    created_date NVARCHAR(50) NOT NULL
);

-- Create HumanApprovalQueue table
CREATE TABLE HumanApprovalQueue (
    approval_id NVARCHAR(50) PRIMARY KEY,
    type NVARCHAR(100) NOT NULL,
    student_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Students(id),
    amount DECIMAL(18, 2) NOT NULL,
    priority NVARCHAR(20) NOT NULL DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH
    age_hours INT NOT NULL DEFAULT 0,
    details NVARCHAR(500) NOT NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'PENDING' -- PENDING, APPROVED, REJECTED
);

-- Create KafkaEvents table for audit trails and telemetry streaming
CREATE TABLE KafkaEvents (
    event_id INT IDENTITY(1,1) PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT GETDATE(),
    topic NVARCHAR(100) NOT NULL,
    payload NVARCHAR(MAX) NOT NULL
);

-- =========================================================================
-- Populate Initial Mock Data for Testing
-- =========================================================================

INSERT INTO Students (id, name, program, semester, email, phone, billed_amount, scholarship_amount, paid_amount, late_fees, currency) VALUES 
('STU-2021-4892', 'Arjun Shah', 'B.Tech CSE', 7, 'arjun.shah@university.edu', '+91 98765 43210', 195000.00, 30000.00, 150000.00, 0.00, 'INR'),
('STU-2022-1082', 'Sarah Connor', 'M.Sc Data Science', 3, 'sarah.c@university.edu', '+1 555-0199', 250000.00, 0.00, 200000.00, 1500.00, 'USD');

INSERT INTO Transactions (txn_id, student_id, date, category, amount, method, status) VALUES 
('TXN-10023', 'STU-2021-4892', '12 May 2026', 'Tuition Fee Sem 7', 150000.00, 'Net Banking', 'APPROVED'),
('TXN-10008', 'STU-2021-4892', '10 Jan 2026', 'Tuition Fee Sem 6', 180000.00, 'Credit Card', 'APPROVED'),
('TXN-20091', 'STU-2022-1082', '05 May 2026', 'Tuition Fee Sem 3', 200000.00, 'SWIFT Transfer', 'APPROVED');

INSERT INTO Refunds (request_id, student_id, description, submitted_date, amount, stage, eta_days) VALUES 
('REF-2026-0901', 'STU-2021-4892', 'Double Payment Refund', '14 May 2026', 150000.00, 'VERIFICATION', 10);

INSERT INTO RefundHistory (request_id, status, date, action_by) VALUES 
('REF-2026-0901', 'SUBMITTED', '14 May 2026', 'Student'),
('REF-2026-0901', 'VERIFICATION', '15 May 2026', 'System Agent');

INSERT INTO LoanLetters (letter_id, student_id, program, amount, bank, status, generated_on, download_url) VALUES 
('LOAN-2026-05', 'STU-2021-4892', 'B.Tech CSE', 195000.00, 'State Bank of India', 'APPROVED', '10 May 2026', '/downloads/loan-demand-STU-2021-4892.pdf');

INSERT INTO ReconciliationExceptions (exception_id, txn_id, student_id, expected, received, delta, source, status, created_date) VALUES 
('EXC-8812', 'TXN-99882', 'STU-2021-4892', 45000.00, 0.00, -45000.00, 'Razorpay Gateway', 'UNMATCHED', '18 May 2026');

INSERT INTO HumanApprovalQueue (approval_id, type, student_id, amount, priority, age_hours, details, status) VALUES 
('APP-9011', 'Refund Approval (High Value)', 'STU-2021-4892', 150000.00, 'HIGH', 12, 'Refund request for double tuition payment sem 7.', 'PENDING');
