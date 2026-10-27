import os
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.security import hash_password
from app.db.database import Base, engine, get_db
from app.models.attendance import Attendance, Shift
from app.models.attrition_history import AttritionHistory
from app.models.audit_log import AuditLog
from app.models.chat import ChatMessage
from app.models.department import Department
from app.models.document import EmployeeDocument
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest
from app.models.notification import Notification
from app.models.payroll import Payroll
from app.models.performance import PerformanceReview
from app.models.task import Task
from app.models.user import User, UserRole

def seed_all():
    print("🌱 Starting Workforce AI Pro Enterprise Tamil Data Seeder...")
    Base.metadata.create_all(bind=engine)
    session = next(get_db())

    # 1. Admin User
    admin = session.query(User).filter(User.email == "pasupathi@gmail.com").first()
    if not admin:
        admin = User(
            full_name="Pasupathi Pandian",
            email="pasupathi@gmail.com",
            hashed_password=hash_password("Root123@"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
    print(f"✓ Admin ready: {admin.full_name} (ID: {admin.id})")

    # 2. Departments
    dept_names = [
        ("Engineering", "Core software development, cloud infrastructure, and DevOps architecture."),
        ("Artificial Intelligence & Data", "Machine learning, NLP research, and workforce intelligence systems."),
        ("Product & Design", "UI/UX engineering, user experience research, and product lifecycle."),
        ("Human Resources", "People operations, talent acquisition, culture, and compliance."),
        ("Sales & Marketing", "Enterprise partnerships, regional expansion, and client solutions."),
        ("Finance & Operations", "Fiscal management, payroll disbursements, and operational logistics."),
    ]
    depts = {}
    for name, desc in dept_names:
        d = session.query(Department).filter(Department.name == name).first()
        if not d:
            d = Department(name=name, description=desc, is_active=True)
            session.add(d)
            session.commit()
            session.refresh(d)
        depts[name] = d
    print(f"✓ {len(depts)} Departments seeded.")

    # 3. Shifts
    shifts_data = [
        ("General Shift", time(9, 0), time(18, 0)),
        ("Morning Shift", time(6, 0), time(15, 0)),
        ("Evening Shift", time(14, 0), time(23, 0)),
        ("Night Shift", time(22, 0), time(7, 0)),
    ]
    shifts = []
    for s_name, s_start, s_end in shifts_data:
        s = session.query(Shift).filter(Shift.name == s_name).first()
        if not s:
            s = Shift(name=s_name, start_time=s_start, end_time=s_end, is_active=True)
            session.add(s)
            session.commit()
            session.refresh(s)
        shifts.append(s)
    print(f"✓ {len(shifts)} Shifts ready.")

    # 4. Tamil Employees List
    tamil_employees_data = [
        {
            "name": "Karthikeyan Ramasamy",
            "email": "karthik.r@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Engineering",
            "code": "EMP-TN101",
            "designation": "Lead Backend Architect",
            "joining": date(2021, 3, 15),
            "salary": Decimal("98000.00"),
            "phone": "+91 98401 23456",
        },
        {
            "name": "Priya Sundaram",
            "email": "priya.s@workforce.ai",
            "role": UserRole.MANAGER,
            "dept": "Product & Design",
            "code": "EMP-TN102",
            "designation": "Staff UX Architect",
            "joining": date(2021, 7, 10),
            "salary": Decimal("92000.00"),
            "phone": "+91 98402 34567",
        },
        {
            "name": "Saravanan Muthu",
            "email": "saravanan.m@workforce.ai",
            "role": UserRole.HR,
            "dept": "Human Resources",
            "code": "EMP-TN103",
            "designation": "People Ops Director",
            "joining": date(2020, 2, 20),
            "salary": Decimal("105000.00"),
            "phone": "+91 98403 45678",
        },
        {
            "name": "Anitha Velmurugan",
            "email": "anitha.v@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Artificial Intelligence & Data",
            "code": "EMP-TN104",
            "designation": "Senior ML Engineer",
            "joining": date(2022, 5, 12),
            "salary": Decimal("89000.00"),
            "phone": "+91 98404 56789",
        },
        {
            "name": "Vignesh Selvam",
            "email": "vignesh.s@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Engineering",
            "code": "EMP-TN105",
            "designation": "DevOps & Cloud Specialist",
            "joining": date(2023, 1, 18),
            "salary": Decimal("84000.00"),
            "phone": "+91 98405 67890",
        },
        {
            "name": "Divya Natarajan",
            "email": "divya.n@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Engineering",
            "code": "EMP-TN106",
            "designation": "Frontend Systems Engineer",
            "joining": date(2022, 9, 5),
            "salary": Decimal("78000.00"),
            "phone": "+91 98406 78901",
        },
        {
            "name": "Murugan Palanichamy",
            "email": "murugan.p@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Finance & Operations",
            "code": "EMP-TN107",
            "designation": "Senior Operations Analyst",
            "joining": date(2021, 11, 25),
            "salary": Decimal("75000.00"),
            "phone": "+91 98407 89012",
        },
        {
            "name": "Kaviya Rajendran",
            "email": "kaviya.r@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Sales & Marketing",
            "code": "EMP-TN108",
            "designation": "Enterprise Account Manager",
            "joining": date(2022, 8, 14),
            "salary": Decimal("82000.00"),
            "phone": "+91 98408 90123",
        },
        {
            "name": "Senthil Kumar",
            "email": "senthil.k@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Artificial Intelligence & Data",
            "code": "EMP-TN109",
            "designation": "NLP Data Scientist",
            "joining": date(2023, 4, 1),
            "salary": Decimal("87000.00"),
            "phone": "+91 98409 01234",
        },
        {
            "name": "Lakshmi Narayanan",
            "email": "lakshmi.n@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Engineering",
            "code": "EMP-TN110",
            "designation": "Security & Compliance Engineer",
            "joining": date(2022, 12, 10),
            "salary": Decimal("86000.00"),
            "phone": "+91 98410 12345",
        },
        {
            "name": "Dinesh Chandran",
            "email": "dinesh.c@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Product & Design",
            "code": "EMP-TN111",
            "designation": "UI Motion Designer",
            "joining": date(2024, 2, 1),
            "salary": Decimal("68000.00"),
            "phone": "+91 98411 23456",
        },
        {
            "name": "Meenakshi Krishnan",
            "email": "meenakshi.k@workforce.ai",
            "role": UserRole.EMPLOYEE,
            "dept": "Human Resources",
            "code": "EMP-TN112",
            "designation": "Talent Acquisition Lead",
            "joining": date(2023, 6, 15),
            "salary": Decimal("72000.00"),
            "phone": "+91 98412 34567",
        },
    ]

    employees = []
    pwd_hash = hash_password("Password@123")

    for item in tamil_employees_data:
        user = session.query(User).filter(User.email == item["email"]).first()
        if not user:
            user = User(
                full_name=item["name"],
                email=item["email"],
                hashed_password=pwd_hash,
                role=item["role"],
                is_active=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        emp = session.query(Employee).filter(Employee.employee_code == item["code"]).first()
        if not emp:
            emp = Employee(
                employee_code=item["code"],
                user_id=user.id,
                department_id=depts[item["dept"]].id,
                designation=item["designation"],
                joining_date=item["joining"],
                salary=item["salary"],
                phone=item["phone"],
                is_active=True,
            )
            session.add(emp)
            session.commit()
            session.refresh(emp)
        employees.append(emp)

    print(f"✓ {len(employees)} Tamil Employees seeded and linked to User accounts.")

    # 5. Populate Tasks & Workflow
    sample_tasks = [
        # Pending
        ("Optimize Postgres Query Indexes", "Profile slow queries on analytics schema and add composite B-Tree indexes.", employees[0].id, "HIGH", "PENDING", date.today() + timedelta(days=3)),
        ("Design Mobile Responsive Layout", "Ensure all dashboard tables degrade gracefully on tablet and mobile viewports.", employees[1].id, "MEDIUM", "PENDING", date.today() + timedelta(days=5)),
        ("Prepare Q4 Campus Hiring Plan", "Draft interview roadmap and criteria for Anna University and PSG Tech hiring.", employees[11].id, "HIGH", "PENDING", date.today() + timedelta(days=7)),
        ("Conduct SOC2 Compliance Check", "Verify server encryption at rest and rotate database root credentials.", employees[9].id, "URGENT", "PENDING", date.today() + timedelta(days=2)),

        # In Progress
        ("Train Attrition ML Pipeline v2", "Include overtime ratios and promotion lag features in random forest estimator.", employees[3].id, "HIGH", "IN_PROGRESS", date.today() + timedelta(days=4)),
        ("Deploy Redis Caching Layer", "Set up Redis cluster for session invalidation and attendance cache.", employees[4].id, "HIGH", "IN_PROGRESS", date.today() + timedelta(days=1)),
        ("Enterprise Contract Drafting", "Finalize annual software licensing agreement for Bangalore enterprise client.", employees[7].id, "MEDIUM", "IN_PROGRESS", date.today() + timedelta(days=6)),
        ("Automate Monthly Tax Deductions", "Implement Form 16 withholding breakdown formulas in payroll engine.", employees[6].id, "URGENT", "IN_PROGRESS", date.today() + timedelta(days=2)),

        # Completed
        ("Migrate Database to MySQL InnoDB", "Successfully converted legacy storage engines and enabled foreign key cascades.", employees[0].id, "URGENT", "COMPLETED", date.today() - timedelta(days=5)),
        ("Implement JWT Auth Bearer Tokens", "Completed access token rotation with HS256 algorithm and role guard.", employees[5].id, "HIGH", "COMPLETED", date.today() - timedelta(days=4)),
        ("Publish HR Policy Handbook 2026", "Circulated updated leave and hybrid working policies to all staff.", employees[2].id, "MEDIUM", "COMPLETED", date.today() - timedelta(days=10)),
        ("Build Donut Chart for Department Stats", "Configured Recharts responsive container with custom hex palette.", employees[1].id, "LOW", "COMPLETED", date.today() - timedelta(days=2)),
    ]

    for title, desc, emp_id, priority, status, due in sample_tasks:
        existing_task = session.query(Task).filter(Task.title == title).first()
        if not existing_task:
            task = Task(
                title=title,
                description=desc,
                assigned_to_id=emp_id,
                created_by_id=admin.id,
                priority=priority,
                status=status,
                due_date=due,
            )
            session.add(task)
    session.commit()
    print("✓ Tasks & Workflow populated (Pending, In Progress, Completed).")

    # 6. Performance Reviews
    reviews_data = [
        (employees[0].id, "Q3 2026", 4.8, "Led backend architecture refactor with 99.98% uptime. High ownership.", "Architectural depth, mentorship, resilience.", "Could delegate operational tasks earlier."),
        (employees[1].id, "Q3 2026", 4.9, "Revamped design system and component libraries. Zero UI regressions.", "Proactive design leadership, fast prototyping.", "Host more cross-functional workshops."),
        (employees[2].id, "Q3 2026", 4.7, "Maintained 94% workforce retention index and streamlined campus hiring.", "Empathetic communication, structured policy enforcement.", "Explore automated HR bots."),
        (employees[3].id, "Q3 2026", 4.5, "Trained Scikit-Learn attrition model with 89% precision score.", "Mathematical modeling, rigorous validation.", "Improve API response schemas documentation."),
        (employees[4].id, "Q3 2026", 4.3, "Automated CI/CD build scripts and reduced deployment window by 40%.", "Infrastructure automation, script optimization.", "Documentation on disaster recovery."),
        (employees[5].id, "Q3 2026", 4.4, "Shipped full React modular UI components ahead of schedule.", "Pixel-perfect implementation, clean code styling.", "Deepen knowledge in backend ORMs."),
        (employees[6].id, "Q3 2026", 4.1, "Managed monthly expense audits and vendor disbursements seamlessly.", "Attention to detail, statutory tax accuracy.", "Adopt automated ledger reconciliations."),
        (employees[7].id, "Q3 2026", 4.6, "Closed 3 major corporate accounts in Tamil Nadu & Karnataka region.", "Strong client negotiation, consistent deal follow-ups.", "Maintain CRM notes daily."),
    ]
    for emp_id, period, rating, feedback, strengths, improvement in reviews_data:
        existing_rev = session.query(PerformanceReview).filter(
            PerformanceReview.employee_id == emp_id,
            PerformanceReview.review_period == period
        ).first()
        if not existing_rev:
            rev = PerformanceReview(
                employee_id=emp_id,
                reviewer_id=admin.id,
                review_period=period,
                rating=rating,
                goals="Target 15% efficiency increase and mentor junior associates.",
                feedback=feedback,
                strengths=strengths,
                improvement_areas=improvement,
                status="COMPLETED",
            )
            session.add(rev)
    session.commit()
    print("✓ Performance Reviews populated with authentic appraisals.")

    # 7. Employee Documents Vault
    docs_data = [
        (employees[0].id, "Employment Offer & Agreement", "CONTRACT", "karthik_employment_contract.pdf", 450.0),
        (employees[0].id, "Aadhaar Identity Card Verification", "ID_PROOF", "karthik_aadhaar_verified.pdf", 280.0),
        (employees[1].id, "Senior UX Architect Master Agreement", "CONTRACT", "priya_contract_2021.pdf", 512.0),
        (employees[1].id, "Passport Copy & Address Proof", "ID_PROOF", "priya_passport_scan.pdf", 320.0),
        (employees[2].id, "Non-Disclosure & Confidentiality Agreement", "CONTRACT", "saravanan_nda_signed.pdf", 390.0),
        (employees[3].id, "IIT Madras M.Tech Degree Certificate", "CERTIFICATE", "anitha_degree_certificate.pdf", 620.0),
        (employees[4].id, "AWS Certified DevOps Professional", "CERTIFICATE", "vignesh_aws_cert.pdf", 310.0),
        (employees[5].id, "Income Tax Declaration Form 12BB", "TAX_FORM", "divya_tax_declaration_2026.pdf", 185.0),
        (employees[6].id, "Chartered Financial Analyst Cert", "CERTIFICATE", "murugan_cfa_cert.pdf", 440.0),
        (employees[7].id, "Updated Curriculum Vitae 2026", "RESUME", "kaviya_resume_executive.pdf", 215.0),
    ]
    for emp_id, title, doc_type, file_name, size in docs_data:
        existing_doc = session.query(EmployeeDocument).filter(
            EmployeeDocument.employee_id == emp_id,
            EmployeeDocument.title == title
        ).first()
        if not existing_doc:
            doc = EmployeeDocument(
                employee_id=emp_id,
                title=title,
                document_type=doc_type,
                file_name=file_name,
                file_path=f"/vault/documents/{doc_type.lower()}/{file_name}",
                file_size_kb=size,
                uploaded_by_id=admin.id,
            )
            session.add(doc)
    session.commit()
    print("✓ Employee Document Vault populated.")

    # 8. Team Chat Messages
    chat_data = [
        (admin.id, None, "general", "Vanakkam team! Welcome to WorkForce AI Pro new platform release. All modules are now active."),
        (employees[0].user_id, None, "general", "Vanakkam sir! The new system looks blazing fast. DB migrations are fully stable."),
        (employees[1].user_id, None, "general", "Great work team! UI feels super responsive. I've uploaded the new Q4 component assets to the vault."),
        (employees[2].user_id, None, "general", "Reminder: October attendance cut-off is on Friday. Please ensure all clock-in punches are logged."),
        (employees[3].user_id, None, "general", "Attrition ML pipeline retraining is complete with 89% accuracy. Predictions are live."),
        (employees[4].user_id, None, "general", "Redis cache layer deployment was successful on production servers."),

        # HR Announcements Channel
        (employees[2].user_id, None, "announcements", "📢 Important Announcement: Deepavali Festival Holidays approved from Nov 1st to Nov 4th."),
        (admin.id, None, "announcements", "Bonus disbursements for festive month will be credited along with October payroll on Oct 30th."),

        # Direct messages (between Karthik & Priya)
        (employees[0].user_id, employees[1].user_id, "direct", "Hi Priya, can you review the new Leave application modal designs?"),
        (employees[1].user_id, employees[0].user_id, "direct", "Sure Karthik, reviewed and verified! The padding and colors look great."),
    ]
    for s_id, r_id, channel, msg in chat_data:
        m = ChatMessage(
            sender_id=s_id,
            receiver_id=r_id,
            channel=channel,
            message=msg,
            is_read=True,
            created_at=datetime.now() - timedelta(minutes=15),
        )
        session.add(m)
    session.commit()
    print("✓ Team Chat conversations populated.")

    # 9. Attendance Logs
    today = date.today()
    for i, emp in enumerate(employees):
        # Today's punch
        status = "PRESENT"
        check_in_hour = 9
        check_in_min = 10 + (i * 2)
        if i == 4 or i == 8:
            status = "LATE"
            check_in_hour = 9
            check_in_min = 45

        check_in_dt = datetime.combine(today, time(check_in_hour, check_in_min))
        check_out_dt = datetime.combine(today, time(18, 15)) if i < 8 else None
        hours = 9.0 if check_out_dt else 0.0
        ot = 1.0 if check_out_dt else 0.0

        existing_att = session.query(Attendance).filter(
            Attendance.employee_id == emp.id, Attendance.date == today
        ).first()
        if not existing_att:
            att = Attendance(
                employee_id=emp.id,
                shift_id=shifts[0].id,
                date=today,
                check_in=check_in_dt,
                check_out=check_out_dt,
                working_hours=hours,
                overtime_hours=ot,
                status=status,
                notes="Biometric verified punch." if status == "PRESENT" else "Traffic delay at Guindy junction.",
            )
            session.add(att)

        # Yesterday's punch
        yesterday = today - timedelta(days=1)
        existing_att_y = session.query(Attendance).filter(
            Attendance.employee_id == emp.id, Attendance.date == yesterday
        ).first()
        if not existing_att_y:
            att_y = Attendance(
                employee_id=emp.id,
                shift_id=shifts[0].id,
                date=yesterday,
                check_in=datetime.combine(yesterday, time(9, 5)),
                check_out=datetime.combine(yesterday, time(18, 30)),
                working_hours=9.4,
                overtime_hours=1.4,
                status="PRESENT",
                notes="Regular shift completed.",
            )
            session.add(att_y)

    session.commit()
    print("✓ Daily Attendance & Shift punches seeded.")

    # 10. Leave Balances & Requests
    for emp in employees:
        bal = session.query(LeaveBalance).filter(LeaveBalance.employee_id == emp.id).first()
        if not bal:
            bal = LeaveBalance(
                employee_id=emp.id,
                year=2026,
                casual_leave=12,
                sick_leave=10,
                annual_leave=15,
                used_casual=2,
                used_sick=1,
                used_annual=3,
            )
            session.add(bal)
    session.commit()

    sample_leaves = [
        (employees[0].id, "CASUAL", today + timedelta(days=5), today + timedelta(days=6), 2.0, "Attending family temple festival in Madurai.", "APPROVED"),
        (employees[3].id, "ANNUAL", today + timedelta(days=10), today + timedelta(days=14), 5.0, "Annual family vacation to Kodaikanal.", "PENDING"),
        (employees[4].id, "SICK", today - timedelta(days=7), today - timedelta(days=6), 2.0, "Viral fever and doctor consultation.", "APPROVED"),
        (employees[7].id, "CASUAL", today + timedelta(days=3), today + timedelta(days=3), 1.0, "Personal administrative banking work in Coimbatore.", "PENDING"),
        (employees[8].id, "UNPAID", today - timedelta(days=14), today - timedelta(days=13), 2.0, "Extended travel without advance notice.", "REJECTED"),
    ]
    for emp_id, l_type, s_date, e_date, days, reason, l_status in sample_leaves:
        existing_l = session.query(LeaveRequest).filter(
            LeaveRequest.employee_id == emp_id, LeaveRequest.start_date == s_date
        ).first()
        if not existing_l:
            lr = LeaveRequest(
                employee_id=emp_id,
                leave_type=l_type,
                start_date=s_date,
                end_date=e_date,
                days_count=days,
                reason=reason,
                status=l_status,
                reviewed_by_id=admin.id,
            )
            session.add(lr)
    session.commit()
    print("✓ Leave Balances & Requests seeded.")

    # 11. Payroll Records
    for emp in employees:
        for month in ["2026-10", "2026-09"]:
            existing_p = session.query(Payroll).filter(
                Payroll.employee_id == emp.id, Payroll.month == month
            ).first()
            if not existing_p:
                basic = emp.salary
                allowances = Decimal("6000.00")
                bonus = Decimal("5000.00") if month == "2026-10" else Decimal("0.00")
                deductions = Decimal("2400.00")
                tax = round((basic + allowances + bonus) * Decimal("0.10"), 2)
                net = (basic + allowances + bonus) - deductions - tax
                p_status = "PAID" if month == "2026-09" else "PROCESSED"
                p = Payroll(
                    employee_id=emp.id,
                    month=month,
                    basic_salary=basic,
                    allowances=allowances,
                    bonus=bonus,
                    deductions=deductions,
                    tax=tax,
                    net_salary=net,
                    status=p_status,
                    payment_date=date(2026, 9, 30) if month == "2026-09" else date(2026, 10, 31),
                    payment_method="NEFT Bank Transfer",
                    notes="Statutory PF & TDS deducted.",
                )
                session.add(p)
    session.commit()
    print("✓ Payroll records generated for October & September.")

    # 12. Attrition AI Prediction History (Realistic Kaggle Model Data)
    attrition_sample_records = [
        # High Risk
        (employees[4].id, 0.84, 84.0, "HIGH", "RandomForestClassifier (v1.0.0)"),
        (employees[8].id, 0.78, 78.0, "HIGH", "RandomForestClassifier (v1.0.0)"),
        (employees[10].id, 0.73, 73.0, "HIGH", "RandomForestClassifier (v1.0.0)"),

        # Medium Risk
        (employees[0].id, 0.54, 54.0, "MEDIUM", "RandomForestClassifier (v1.0.0)"),
        (employees[3].id, 0.48, 48.0, "MEDIUM", "RandomForestClassifier (v1.0.0)"),
        (employees[6].id, 0.44, 44.0, "MEDIUM", "RandomForestClassifier (v1.0.0)"),
        (employees[7].id, 0.52, 52.0, "MEDIUM", "RandomForestClassifier (v1.0.0)"),

        # Low Risk
        (employees[1].id, 0.14, 14.0, "LOW", "RandomForestClassifier (v1.0.0)"),
        (employees[2].id, 0.18, 18.0, "LOW", "RandomForestClassifier (v1.0.0)"),
        (employees[5].id, 0.22, 22.0, "LOW", "RandomForestClassifier (v1.0.0)"),
        (employees[9].id, 0.19, 19.0, "LOW", "RandomForestClassifier (v1.0.0)"),
        (employees[11].id, 0.25, 25.0, "LOW", "RandomForestClassifier (v1.0.0)"),
    ]
    for emp_id, prob, risk_pct, level, model_name in attrition_sample_records:
        existing_att_rec = session.query(AttritionHistory).filter(
            AttritionHistory.employee_id == emp_id
        ).first()
        if not existing_att_rec:
            ah = AttritionHistory(
                employee_id=emp_id,
                predicted_by_user_id=admin.id,
                attrition_probability=prob,
                attrition_risk_percentage=risk_pct,
                risk_level=level,
                model_type=model_name,
            )
            session.add(ah)
    session.commit()
    print("✓ Attrition AI Prediction History populated with High/Medium/Low flight risk strata.")

    # 13. System Notifications
    notifications_list = [
        (None, "Diwali Festival Holiday Notice", "Office will remain closed from November 1st to November 4th. Advance wishes to all staff!", "INFO", "HIGH"),
        (admin.id, "High Risk Turnover Alert", "AI Engine flagged Vignesh Selvam & Senthil Kumar above 75% attrition threshold.", "ALERT", "URGENT"),
        (None, "October Monthly Payroll Dispatched", "October 2026 payroll generated and processed for 12 employees via NEFT.", "SUCCESS", "MEDIUM"),
        (employees[0].user_id, "Leave Application Approved", "Your Casual Leave application for Madurai temple visit is approved.", "SUCCESS", "LOW"),
    ]
    for u_id, title, message, n_type, priority in notifications_list:
        n = Notification(
            user_id=u_id,
            title=title,
            message=message,
            type=n_type,
            priority=priority,
            is_read=False,
        )
        session.add(n)
    session.commit()
    print("✓ Notifications created.")

    # 14. Audit Logs
    audit_events = [
        ("LOGIN_SUCCESS", "USER", admin.id, "Admin logged into WorkForce AI Pro portal from Chennai."),
        ("BATCH_PAYROLL_GENERATE", "PAYROLL", None, "Generated 12 salary records for month 2026-10."),
        ("ATTRITION_PREDICTION_RUN", "AI_MODEL", None, "Executed Random Forest inference across all department cohorts."),
        ("LEAVE_APPROVED", "LEAVE_REQUEST", 1, "Admin approved 2 days casual leave for Karthikeyan Ramasamy."),
        ("DOCUMENT_UPLOAD", "EMPLOYEE_DOCUMENT", 1, "Uploaded Employment contract PDF to secure vault."),
    ]
    for act, target, t_id, details in audit_events:
        al = AuditLog(
            user_id=admin.id,
            action=act,
            target_type=target,
            target_id=t_id,
            details=details,
            ip_address="127.0.0.1",
        )
        session.add(al)
    session.commit()
    print("✓ Audit trail logged.")

    print("\n🎉 ALL WORKFORCE DATA SUCCESSFULLY SEEDED WITH AUTHENTIC TAMIL PROFILES!")

if __name__ == "__main__":
    seed_all()
