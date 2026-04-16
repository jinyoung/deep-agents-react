#!/usr/bin/env python3
"""
Generate 8 sample English PDFs for 6 use cases.
Uses fpdf2 to create realistic test documents.
"""

import os
from pathlib import Path

from fpdf import FPDF

OUT = Path("sample_pdfs")
OUT.mkdir(exist_ok=True)


class DocPDF(FPDF):
    """Base PDF with consistent styling."""

    def header(self):
        if hasattr(self, "_doc_title") and self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 5, self._doc_title, align="R")
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self, title, subtitle="", date=""):
        self.add_page()
        self.ln(60)
        self.set_font("Helvetica", "B", 24)
        self.multi_cell(0, 12, title, align="C")
        if subtitle:
            self.ln(5)
            self.set_font("Helvetica", "", 14)
            self.multi_cell(0, 8, subtitle, align="C")
        if date:
            self.ln(10)
            self.set_font("Helvetica", "", 12)
            self.cell(0, 8, date, align="C")

    def heading(self, text, level=1):
        sizes = {1: 16, 2: 13, 3: 11}
        self.ln(4)
        self.set_font("Helvetica", "B", sizes.get(level, 11))
        self.multi_cell(0, 7, text)
        self.ln(2)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            w = (self.w - 20) / len(headers)
            col_widths = [w] * len(headers)
        self.set_font("Helvetica", "B", 9)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align="C")
        self.ln()
        self.set_font("Helvetica", "", 9)
        for row in rows:
            for i, c in enumerate(row):
                self.cell(col_widths[i], 6, str(c), border=1)
            self.ln()
        self.ln(3)


# ─────────────────────────────────────────────────────
# PDF 1: Nuclear Power Terminology Reference
# ─────────────────────────────────────────────────────
def gen_terminology():
    pdf = DocPDF()
    pdf._doc_title = "Nuclear Power Terminology Guide v2.3"
    pdf.alias_nb_pages()

    pdf.title_page(
        "KEPCO E&C",
        "Overseas Nuclear Power Project\nTerminology Guide v2.3",
        "Effective Date: January 2024",
    )

    terms = [
        ("PWR (Pressurized Water Reactor)",
         "A type of light-water nuclear reactor that uses ordinary water under high pressure as both coolant and neutron moderator. The primary coolant loop is kept under high pressure to prevent boiling.",
         "The Barakah Units 1-4 utilize PWR technology based on the APR-1400 design.",
         "Incorrect: 'PWR uses heavy water as moderator' - PWR uses light (ordinary) water."),
        ("Steam Generator (SG)",
         "A heat exchanger that transfers thermal energy from the primary reactor coolant to the secondary side to produce steam for the turbine. Each PWR unit typically has 2-4 steam generators.",
         "Steam generator tube integrity inspection is performed during each refueling outage.",
         "Incorrect: 'Steam generators produce nuclear reactions' - SGs only transfer heat."),
        ("NSSS (Nuclear Steam Supply System)",
         "The complete system that generates steam from nuclear fission, including the reactor vessel, steam generators, reactor coolant pumps, pressurizer, and associated piping.",
         "The NSSS vendor is responsible for the reactor island design and key nuclear components.",
         "Incorrect: 'NSSS includes the turbine island' - NSSS covers only the nuclear side."),
        ("Containment Building",
         "A gas-tight, steel-lined reinforced concrete structure enclosing the nuclear reactor. Designed to contain radioactive materials in case of an accident and to protect the reactor from external events.",
         "The containment building withstands internal pressure of 4.5 bar (absolute) design pressure.",
         "Incorrect: 'Containment is only for radiation shielding' - It also prevents release."),
        ("DBA (Design Basis Accident)",
         "A postulated accident that a nuclear facility must be designed and built to withstand without exceeding regulatory dose limits at the site boundary.",
         "The DBA analysis includes LOCA, steam line break, and control rod ejection scenarios.",
         "Incorrect: 'DBA means the most severe possible accident' - DBA is a design reference, not worst case."),
        ("LOCA (Loss of Coolant Accident)",
         "An accident resulting from a breach in the reactor coolant system pressure boundary, causing coolant loss at a rate exceeding the normal makeup capacity.",
         "Emergency Core Cooling System (ECCS) is designed to mitigate the consequences of a LOCA.",
         "Incorrect: 'LOCA only refers to small pipe breaks' - LOCA includes all sizes up to double-ended guillotine break."),
        ("BOP (Balance of Plant)",
         "All systems and components of a power plant excluding the Nuclear Steam Supply System (NSSS). Includes turbine-generator, condenser, feedwater system, cooling water system, and electrical systems.",
         "The BOP contractor is responsible for the turbine island and common facilities.",
         "Incorrect: 'BOP includes the reactor vessel' - The reactor is part of NSSS, not BOP."),
        ("RCP (Reactor Coolant Pump)",
         "A pump that circulates reactor coolant through the reactor core and steam generators in a PWR. Each coolant loop has one RCP. The APR-1400 has four RCPs.",
         "RCP seal integrity is critical for preventing small-break LOCA events.",
         "Incorrect: 'RCP operates only during power operation' - RCP may also run during shutdown cooling."),
        ("Seismic Category I",
         "The highest seismic design classification for nuclear plant structures, systems, and components (SSCs). Category I SSCs must remain functional during and after a Safe Shutdown Earthquake (SSE).",
         "The containment building, reactor vessel, and ECCS are all classified as Seismic Category I.",
         "Incorrect: 'Seismic Category I is the lowest classification' - It is the HIGHEST."),
        ("Turbine Island",
         "The portion of a nuclear power plant containing the steam turbine, generator, condenser, feedwater heaters, and associated systems that convert steam energy into electrical power.",
         "The turbine island is part of the Balance of Plant (BOP) scope.",
         "Incorrect: 'Turbine Island handles nuclear fuel' - Fuel is handled in the reactor/fuel building."),
    ]

    # Terms pages
    for i, (name, defn, usage, error) in enumerate(terms):
        if i % 3 == 0:
            pdf.add_page()
        pdf.heading(f"{i+1}. {name}", 2)
        pdf.body(f"Definition: {defn}")
        pdf.body(f"Usage Example: {usage}")
        pdf.body(f"Common Error: {error}")
        pdf.ln(2)

    # Q&A page
    pdf.add_page()
    pdf.heading("Terminology Q&A (10 Questions)", 1)

    qas = [
        ("Q1: What type of water does a PWR use as moderator?",
         "A1: Light (ordinary) water under high pressure."),
        ("Q2: What is the primary function of a Steam Generator?",
         "A2: To transfer heat from primary coolant to secondary side to produce steam."),
        ("Q3: Does the NSSS include the turbine-generator?",
         "A3: No. NSSS covers only the nuclear steam supply side (reactor, SGs, RCPs, pressurizer)."),
        ("Q4: What is the purpose of the Containment Building?",
         "A4: To contain radioactive materials and protect the reactor from external events."),
        ("Q5: Is a DBA the worst possible accident scenario?",
         "A5: No. DBA is a design reference accident, not the most severe beyond-design-basis event."),
        ("Q6: Does LOCA only refer to small pipe breaks?",
         "A6: No. LOCA includes all break sizes up to double-ended guillotine break (DEGB)."),
        ("Q7: Is the reactor vessel part of the BOP scope?",
         "A7: No. The reactor vessel is part of NSSS. BOP covers non-nuclear systems."),
        ("Q8: How many RCPs does the APR-1400 have?",
         "A8: Four RCPs, one per coolant loop."),
        ("Q9: Is Seismic Category I the lowest or highest classification?",
         "A9: It is the HIGHEST seismic design classification."),
        ("Q10: Does the Turbine Island handle nuclear fuel?",
         "A10: No. Nuclear fuel is handled in the reactor building and fuel building."),
    ]

    for q, a in qas:
        pdf.body(q)
        pdf.body(a)
        pdf.ln(1)

    pdf.output(str(OUT / "Nuclear_Power_Terminology_Reference.pdf"))
    print("  [1/8] Nuclear_Power_Terminology_Reference.pdf")


# ─────────────────────────────────────────────────────
# PDF 2: Audit Report with Financial Statements
# ─────────────────────────────────────────────────────
def gen_audit_report():
    pdf = DocPDF()
    pdf._doc_title = "SAPCO 2024 Audit Report"
    pdf.alias_nb_pages()

    pdf.title_page(
        "Shuweihat Asia Power Company PJSC",
        "Independent Auditor's Report and\nFinancial Statements\nFor the Year Ended December 31, 2024",
        "Auditor: Deloitte & Touche (M.E.)",
    )

    # Auditor's Report
    pdf.add_page()
    pdf.heading("Independent Auditor's Report", 1)
    pdf.body("To the Shareholders of Shuweihat Asia Power Company PJSC")
    pdf.body(
        "Opinion\n\n"
        "We have audited the financial statements of Shuweihat Asia Power Company PJSC "
        "(the 'Company'), which comprise the statement of financial position as at "
        "December 31, 2024, and the statement of profit or loss and other comprehensive "
        "income, statement of changes in equity and statement of cash flows for the year "
        "then ended, and notes to the financial statements.\n\n"
        "In our opinion, the accompanying financial statements present fairly, in all "
        "material respects, the financial position of the Company as at December 31, 2024, "
        "and its financial performance and cash flows for the year then ended in accordance "
        "with International Financial Reporting Standards (IFRS)."
    )
    pdf.body(
        "Basis for Opinion\n\n"
        "We conducted our audit in accordance with International Standards on Auditing (ISAs). "
        "Our responsibilities under those standards are further described in the Auditor's "
        "Responsibilities section. We are independent of the Company and have fulfilled our "
        "ethical responsibilities in accordance with the IESBA Code of Ethics."
    )

    # Statement of Financial Position
    pdf.add_page()
    pdf.heading("Statement of Financial Position", 1)
    pdf.heading("As at December 31, 2024 (Amounts in AED thousands)", 3)

    pdf.heading("ASSETS", 2)
    pdf.heading("Non-current Assets", 3)
    pdf.table(
        ["Item", "2024", "2023"],
        [
            ["Property, plant and equipment", "3,085,000", "3,245,000"],
            ["Right-of-use assets", "156,200", "168,400"],
            ["Intangible assets", "89,500", "94,200"],
            ["Deferred tax assets", "12,300", "11,800"],
            ["Other non-current assets", "498,200", "512,300"],
            ["Total Non-current Assets", "3,841,200", "4,031,700"],
        ],
        [80, 50, 50],
    )

    pdf.heading("Current Assets", 3)
    pdf.table(
        ["Item", "2024", "2023"],
        [
            ["Trade and other receivables", "245,800", "231,400"],
            ["Inventories", "67,300", "58,900"],
            ["Cash and cash equivalents", "189,500", "142,300"],
            ["Other current assets", "34,200", "29,100"],
            ["Total Current Assets", "536,800", "461,700"],
        ],
        [80, 50, 50],
    )

    pdf.body("TOTAL ASSETS: AED 4,378,000 thousand (2023: AED 4,493,400 thousand)")

    # Liabilities & Equity
    pdf.add_page()
    pdf.heading("EQUITY AND LIABILITIES", 2)
    pdf.heading("Equity", 3)
    pdf.table(
        ["Item", "2024", "2023"],
        [
            ["Share capital", "500,000", "500,000"],
            ["Statutory reserve", "250,000", "250,000"],
            ["Retained earnings", "412,600", "384,600"],
            ["Total Equity", "1,162,600", "1,134,600"],
        ],
        [80, 50, 50],
    )

    pdf.heading("Non-current Liabilities", 3)
    pdf.table(
        ["Item", "2024", "2023"],
        [
            ["Long-term borrowings", "2,533,800", "2,689,200"],
            ["Lease liabilities (non-current)", "142,100", "153,800"],
            ["Provision for decommissioning", "198,500", "187,300"],
            ["Total Non-current Liabilities", "2,874,400", "3,030,300"],
        ],
        [80, 50, 50],
    )

    pdf.heading("Current Liabilities", 3)
    pdf.table(
        ["Item", "2024", "2023"],
        [
            ["Trade and other payables", "156,200", "148,700"],
            ["Current portion of borrowings", "155,400", "152,100"],
            ["Lease liabilities (current)", "14,200", "13,500"],
            ["Accrued expenses", "15,200", "14,200"],
            ["Total Current Liabilities", "341,000", "328,500"],
        ],
        [80, 50, 50],
    )

    pdf.body("TOTAL EQUITY AND LIABILITIES: AED 4,378,000 thousand (2023: AED 4,493,400 thousand)")

    # Income Statement
    pdf.add_page()
    pdf.heading("Statement of Profit or Loss", 1)
    pdf.heading("For the Year Ended December 31, 2024 (AED thousands)", 3)
    pdf.table(
        ["Item", "2024", "2023"],
        [
            ["Revenue from power generation", "487,200", "441,300"],
            ["Revenue from water desalination", "50,000", "60,400"],
            ["Total Revenue", "537,200", "501,700"],
            ["Cost of sales", "(322,500)", "(315,200)"],
            ["Gross Profit", "214,700", "186,500"],
            ["General and administrative expenses", "(42,300)", "(39,800)"],
            ["Depreciation and amortization", "(124,400)", "(128,600)"],
            ["Other operating expenses", "(20,000)", "(18,700)"],
            ["Operating Profit", "28,000", "(600)"],
            ["Finance costs", "(89,200)", "(95,400)"],
            ["Finance income", "3,200", "2,100"],
            ["Profit / (Loss) before tax", "(58,000)", "(93,900)"],
            ["Income tax expense", "0", "0"],
            ["Net Profit / (Loss) for the year", "(58,000)", "(93,900)"],
        ],
        [80, 50, 50],
    )

    # Cash Flow
    pdf.add_page()
    pdf.heading("Statement of Cash Flows", 1)
    pdf.heading("For the Year Ended December 31, 2024 (AED thousands)", 3)
    pdf.table(
        ["Item", "2024", "2023"],
        [
            ["Operating Activities", "", ""],
            ["Profit/(Loss) before tax", "(58,000)", "(93,900)"],
            ["Depreciation and amortization", "124,400", "128,600"],
            ["Finance costs", "89,200", "95,400"],
            ["Changes in working capital", "(12,300)", "8,200"],
            ["Net cash from operating activities", "143,300", "138,300"],
            ["", "", ""],
            ["Investing Activities", "", ""],
            ["Purchase of property, plant, equipment", "(15,800)", "(22,100)"],
            ["Net cash used in investing", "(15,800)", "(22,100)"],
            ["", "", ""],
            ["Financing Activities", "", ""],
            ["Repayment of borrowings", "(152,100)", "(148,500)"],
            ["Lease payments", "(17,200)", "(16,800)"],
            ["Finance costs paid", "(89,200)", "(95,400)"],
            ["Dividends paid", "(30,000)", "0"],
            ["Net cash used in financing", "(288,500)", "(260,700)"],
            ["", "", ""],
            ["Net decrease in cash", "(160,700)", "(144,500)"],
            ["Cash at beginning of year", "142,300", "286,800"],
            ["Cash at end of year", "189,500", "142,300"],
        ],
        [80, 50, 50],
    )

    # Notes
    pdf.add_page()
    pdf.heading("Notes to the Financial Statements", 1)
    pdf.heading("1. General Information", 2)
    pdf.body(
        "Shuweihat Asia Power Company PJSC (the 'Company') was incorporated in Abu Dhabi, "
        "United Arab Emirates on March 15, 2004. The Company operates a 1,500 MW power "
        "generation and 100 MIGD water desalination plant in Al Ruwais Industrial City."
    )
    pdf.heading("2. Basis of Preparation", 2)
    pdf.body(
        "The financial statements have been prepared in accordance with International "
        "Financial Reporting Standards (IFRS) as issued by the International Accounting "
        "Standards Board (IASB). The financial statements are presented in UAE Dirhams (AED) "
        "and all values are rounded to the nearest thousand."
    )
    pdf.heading("11. Property, Plant and Equipment", 2)
    pdf.body(
        "The Company's power plant assets are depreciated over the concession period of 25 years. "
        "Major overhaul costs are capitalized and depreciated over the period until the next "
        "scheduled overhaul. The net book value of property, plant and equipment as at "
        "December 31, 2024 is AED 3,085,000 thousand (2023: AED 3,245,000 thousand)."
    )

    pdf.output(str(OUT / "SAPCO_2024_Audit_Report.pdf"))
    print("  [2/8] SAPCO_2024_Audit_Report.pdf")


# ─────────────────────────────────────────────────────
# PDF 3a/3b: EPC Contracts (Alpha / Beta)
# ─────────────────────────────────────────────────────
def _gen_epc_contract(project_name, project_desc, ld_cap, warranty_months, arbitration_body,
                      arbitration_seat, force_majeure_extra, filename, idx):
    pdf = DocPDF()
    pdf._doc_title = f"EPC Contract - {project_name}"
    pdf.alias_nb_pages()

    pdf.title_page(
        f"EPC Contract\n{project_name}",
        project_desc,
        "Contract Date: March 1, 2024",
    )

    # Article 1 - Definitions
    pdf.add_page()
    pdf.heading("Article 1 - Definitions and Interpretation", 1)
    pdf.body(
        "1.1 'Contract Price' means the total lump sum price of USD 4,200,000,000 "
        f"for the {project_name} project.\n\n"
        "1.2 'Completion Date' means the date on which the Works are completed in "
        "accordance with the Contract requirements.\n\n"
        "1.3 'Defects Notification Period' means the period stated in Article 22.\n\n"
        "1.4 'Engineer' means the person appointed by the Employer to administer the Contract.\n\n"
        "1.5 'Employer' means the entity that has entered into this Contract for the construction "
        "of the nuclear power plant."
    )

    # Article 5 - Scope of Work
    pdf.add_page()
    pdf.heading("Article 5 - Scope of Work", 1)
    pdf.body(
        f"5.1 The Contractor shall design, engineer, procure, construct, install, "
        f"test and commission the {project_name} nuclear power plant facility.\n\n"
        "5.2 The scope includes but is not limited to:\n"
        "  (a) Nuclear Steam Supply System (NSSS)\n"
        "  (b) Turbine Island and Balance of Plant (BOP)\n"
        "  (c) Auxiliary systems and supporting facilities\n"
        "  (d) Cooling water intake and outfall structures\n"
        "  (e) Site preparation and civil works\n"
        "  (f) Electrical systems and grid connection\n"
        "  (g) Instrumentation and control systems\n\n"
        "5.3 The Contractor shall obtain all necessary permits and approvals from the "
        "Nuclear Regulatory Authority."
    )

    # Article 8 - Payment
    pdf.add_page()
    pdf.heading("Article 8 - Payment Terms", 1)
    pdf.body(
        "8.1 The Employer shall pay the Contractor the Contract Price in accordance with "
        "the following milestone payment schedule:\n\n"
        "  (a) 10% upon Contract signing (advance payment)\n"
        "  (b) 20% upon completion of engineering design\n"
        "  (c) 30% upon delivery of major equipment to site\n"
        "  (d) 25% upon completion of construction and installation\n"
        "  (e) 10% upon successful hot functional testing\n"
        "  (f) 5% upon final acceptance and handover\n\n"
        "8.2 The Contractor shall submit monthly progress certificates to the Engineer.\n\n"
        "8.3 Payment shall be made within 45 calendar days of certification by the Engineer."
    )

    # Article 12 - Liquidated Damages
    pdf.add_page()
    pdf.heading("Article 12 - Liquidated Damages for Delay", 1)
    pdf.body(
        "12.1 If the Contractor fails to achieve Completion by the Completion Date, "
        "the Contractor shall pay liquidated damages to the Employer at the rate of "
        "0.1% of the Contract Price per day of delay.\n\n"
        f"12.2 The maximum aggregate amount of liquidated damages shall not exceed "
        f"{ld_cap}% of the Contract Price.\n\n"
        "12.3 Payment of liquidated damages shall not relieve the Contractor from its "
        "obligation to complete the Works.\n\n"
        "12.4 Liquidated damages shall be the Employer's sole and exclusive remedy for "
        "delay in completion."
    )

    # Article 15 - Force Majeure
    pdf.add_page()
    pdf.heading("Article 15 - Force Majeure", 1)
    pdf.body(
        "15.1 'Force Majeure' means an event or circumstance beyond the reasonable control "
        "of the affected Party, which could not have been reasonably foreseen or prevented.\n\n"
        "15.2 Force Majeure events include but are not limited to:\n"
        "  (a) War, hostilities, invasion, act of foreign enemies\n"
        "  (b) Rebellion, revolution, insurrection, military or usurped power\n"
        "  (c) Natural catastrophes such as earthquake, flood, volcanic activity\n"
        "  (d) Nuclear explosion, radioactive contamination (excluding from the Works)\n"
        "  (e) Epidemic or pandemic declared by WHO\n"
        f"  {force_majeure_extra}\n\n"
        "15.3 The affected Party shall give notice within 14 days of becoming aware "
        "of the Force Majeure event.\n\n"
        "15.4 If Force Majeure continues for more than 180 consecutive days, either Party "
        "may terminate the Contract by giving 30 days written notice."
    )

    # Article 20 - Dispute Resolution
    pdf.add_page()
    pdf.heading("Article 20 - Dispute Resolution", 1)
    pdf.body(
        "20.1 Any dispute arising out of or in connection with this Contract shall be "
        "settled amicably through good faith negotiation within 30 days.\n\n"
        "20.2 If the dispute is not resolved by negotiation, it shall be referred to "
        "a Dispute Adjudication Board (DAB) consisting of three members.\n\n"
        "20.3 If either Party is dissatisfied with the DAB decision, the dispute shall "
        f"be finally settled by arbitration under the Rules of the {arbitration_body}.\n\n"
        f"20.4 The seat of arbitration shall be {arbitration_seat}.\n\n"
        "20.5 The arbitration shall be conducted in the English language.\n\n"
        "20.6 The arbitral award shall be final and binding on both Parties."
    )

    # Article 22 - Warranty
    pdf.add_page()
    pdf.heading("Article 22 - Defects Notification Period (Warranty)", 1)
    pdf.body(
        f"22.1 The Defects Notification Period shall be {warranty_months} months from "
        f"the date of Taking Over.\n\n"
        "22.2 During the Defects Notification Period, the Contractor shall at its own cost "
        "remedy any defects in the Works that are attributable to defective design, materials, "
        "or workmanship.\n\n"
        "22.3 The Employer shall notify the Contractor of any defect within 14 days of discovery.\n\n"
        "22.4 The Contractor shall commence remedial work within 7 days of receiving "
        "notification and complete the repair within a reasonable timeframe.\n\n"
        f"22.5 For safety-critical nuclear components, the warranty period shall be "
        f"extended to {warranty_months + 12} months."
    )

    # Article 25 - IP
    pdf.add_page()
    pdf.heading("Article 25 - Intellectual Property Rights", 1)
    pdf.body(
        "25.1 All intellectual property rights in the design documents, drawings, and "
        "specifications prepared by the Contractor specifically for the Works shall be "
        "licensed to the Employer for the purpose of operating and maintaining the plant.\n\n"
        "25.2 The Contractor retains ownership of its pre-existing intellectual property.\n\n"
        "25.3 The Contractor shall indemnify the Employer against any claims of IP infringement "
        "arising from the Works."
    )

    pdf.output(str(OUT / filename))
    print(f"  [{idx}/8] {filename}")


def gen_contracts():
    _gen_epc_contract(
        "Project Alpha",
        "Barakah Nuclear Power Plant - Units 5 & 6 Extension\nAbu Dhabi, UAE",
        ld_cap=10,
        warranty_months=24,
        arbitration_body="International Chamber of Commerce (ICC)",
        arbitration_seat="Paris, France",
        force_majeure_extra="(f) Government embargo or sanctions",
        filename="EPC_Contract_ProjectAlpha.pdf",
        idx=3,
    )
    _gen_epc_contract(
        "Project Beta",
        "El Dabaa Nuclear Power Plant - Unit 5\nEl Dabaa, Egypt",
        ld_cap=15,
        warranty_months=36,
        arbitration_body="London Court of International Arbitration (LCIA)",
        arbitration_seat="London, United Kingdom",
        force_majeure_extra="(f) Cyber attack on critical infrastructure\n  (g) Government embargo or sanctions\n  (h) Extreme weather events exceeding design parameters",
        filename="EPC_Contract_ProjectBeta.pdf",
        idx=4,
    )


# ─────────────────────────────────────────────────────
# PDF 5: O&M Service Agreement
# ─────────────────────────────────────────────────────
def gen_om_contract():
    pdf = DocPDF()
    pdf._doc_title = "O&M Service Agreement"
    pdf.alias_nb_pages()

    pdf.title_page(
        "Operations & Maintenance\nService Agreement",
        "Barakah Nuclear Power Plant - Units 1-4\nBetween ENEC and KEPCO KPS",
        "Effective Date: July 1, 2024",
    )

    pdf.add_page()
    pdf.heading("Article 1 - Scope of Services", 1)
    pdf.body(
        "1.1 The Service Provider shall provide comprehensive operations and maintenance "
        "services for Barakah Nuclear Power Plant Units 1 through 4.\n\n"
        "1.2 Services include:\n"
        "  (a) Plant operations management and shift staffing\n"
        "  (b) Preventive and corrective maintenance\n"
        "  (c) Refueling outage planning and execution\n"
        "  (d) Radiation protection and environmental monitoring\n"
        "  (e) Chemistry and waste management\n"
        "  (f) Emergency preparedness and response\n"
        "  (g) Training and qualification of plant personnel"
    )

    pdf.add_page()
    pdf.heading("Article 4 - Performance Guarantees", 1)
    pdf.body(
        "4.1 The Service Provider guarantees the following Key Performance Indicators (KPIs):\n\n"
        "  (a) Capacity Factor: minimum 85% annual average per unit\n"
        "  (b) Forced Outage Rate: maximum 5% per unit\n"
        "  (c) Unplanned Automatic Scrams (UA7): maximum 1 per 7,000 hours critical\n"
        "  (d) Collective Radiation Exposure: maximum 100 person-rem per unit per year\n"
        "  (e) Safety System Performance: greater than 99% availability\n\n"
        "4.2 Performance shall be measured quarterly and reported to the Owner.\n\n"
        "4.3 The Service Provider shall maintain WANO (World Association of Nuclear Operators) "
        "performance indicators at or above the industry median."
    )

    pdf.add_page()
    pdf.heading("Article 5 - Service Level Agreement (SLA)", 1)
    pdf.body(
        "5.1 Response Times for Maintenance Requests:\n\n"
        "  Priority 1 (Safety Critical): Response within 1 hour, resolution within 4 hours\n"
        "  Priority 2 (Production Impact): Response within 4 hours, resolution within 24 hours\n"
        "  Priority 3 (Degraded Condition): Response within 24 hours, resolution within 7 days\n"
        "  Priority 4 (Routine): Response within 48 hours, resolution within 30 days\n\n"
        "5.2 Plant Availability Target:\n"
        "  Annual availability shall not be less than 90% per unit.\n\n"
        "5.3 Reporting Requirements:\n"
        "  (a) Daily plant status report\n"
        "  (b) Weekly maintenance summary\n"
        "  (c) Monthly performance report with KPI dashboard\n"
        "  (d) Quarterly management review presentation\n"
        "  (e) Annual performance assessment report"
    )

    pdf.add_page()
    pdf.heading("Article 8 - Penalty Provisions", 1)
    pdf.body(
        "8.1 Failure to meet the guaranteed Capacity Factor shall result in a penalty of "
        "USD 500,000 per percentage point below the guaranteed level, per unit.\n\n"
        "8.2 Failure to meet SLA response times:\n"
        "  Priority 1 violation: USD 100,000 per occurrence\n"
        "  Priority 2 violation: USD 50,000 per occurrence\n"
        "  Priority 3 violation: USD 10,000 per occurrence\n\n"
        "8.3 The maximum aggregate penalty in any contract year shall not exceed 20% "
        "of the annual service fee.\n\n"
        "8.4 Repeated failure (3 or more Priority 1 violations in any 12-month period) "
        "shall constitute grounds for termination for cause."
    )

    pdf.add_page()
    pdf.heading("Article 12 - Personnel Qualifications", 1)
    pdf.body(
        "12.1 The Service Provider shall ensure all personnel meet the qualification "
        "requirements of the Federal Authority for Nuclear Regulation (FANR).\n\n"
        "12.2 Key Personnel:\n"
        "  (a) Plant Manager: minimum 15 years nuclear power plant experience\n"
        "  (b) Shift Supervisors: SRO license from recognized nuclear regulatory authority\n"
        "  (c) Reactor Operators: RO license with minimum 5 years nuclear experience\n"
        "  (d) Maintenance Supervisors: minimum 10 years relevant experience\n\n"
        "12.3 The Owner shall have the right to approve or reject any Key Personnel proposed "
        "by the Service Provider."
    )

    pdf.add_page()
    pdf.heading("Article 15 - Safety Requirements", 1)
    pdf.body(
        "15.1 The Service Provider shall comply with all applicable FANR regulations.\n\n"
        "15.2 The Service Provider shall maintain a Safety Management System compliant with "
        "IAEA Safety Standard GSR Part 2.\n\n"
        "15.3 Any safety event rated INES Level 1 or above shall be reported to the Owner "
        "within 2 hours of occurrence.\n\n"
        "15.4 The Service Provider shall conduct an annual independent safety review "
        "and provide results to the Owner within 30 days."
    )

    pdf.output(str(OUT / "Service_Agreement_OMContract.pdf"))
    print("  [5/8] Service_Agreement_OMContract.pdf")


# ─────────────────────────────────────────────────────
# PDF 6: Technology License Agreement
# ─────────────────────────────────────────────────────
def gen_license_agreement():
    pdf = DocPDF()
    pdf._doc_title = "Technology License Agreement"
    pdf.alias_nb_pages()

    pdf.title_page(
        "Technology License Agreement",
        "APR-1400 Reactor Technology\nBetween KHNP and Nabda Energy",
        "Effective Date: January 15, 2024",
    )

    pdf.add_page()
    pdf.heading("Article 1 - License Grant", 1)
    pdf.body(
        "1.1 The Licensor hereby grants to the Licensee a non-exclusive, non-transferable "
        "license to use the APR-1400 reactor technology for the design, construction, and "
        "operation of nuclear power plants within the Territory.\n\n"
        "1.2 'Territory' means the Arab Republic of Egypt.\n\n"
        "1.3 The license covers:\n"
        "  (a) Reactor design documentation and technical specifications\n"
        "  (b) Safety analysis methodology and computer codes\n"
        "  (c) Manufacturing and construction procedures\n"
        "  (d) Commissioning and operating procedures\n"
        "  (e) Training materials and programs\n\n"
        "1.4 The license does not include the right to sublicense or export to third countries."
    )

    pdf.add_page()
    pdf.heading("Article 3 - Royalty Structure", 1)
    pdf.body(
        "3.1 The Licensee shall pay the following royalties to the Licensor:\n\n"
        "  (a) Initial License Fee: USD 150,000,000 payable upon Contract signing\n"
        "  (b) Per-Unit Royalty: USD 50,000,000 per reactor unit constructed\n"
        "  (c) Annual Technology Support Fee: USD 5,000,000 per year per operating unit\n"
        "  (d) Training Fee: USD 2,000,000 per training program conducted\n\n"
        "3.2 Royalty payments shall be made within 60 days of invoice.\n\n"
        "3.3 All payments shall be made in US Dollars to the Licensor's designated account.\n\n"
        "3.4 Late payments shall bear interest at SOFR + 2% per annum."
    )

    pdf.add_page()
    pdf.heading("Article 5 - Technical Assistance", 1)
    pdf.body(
        "5.1 The Licensor shall provide the following technical assistance:\n\n"
        "  (a) On-site technical advisors during construction (minimum 20 persons)\n"
        "  (b) Design review and approval support\n"
        "  (c) Licensing support with the Egyptian Nuclear and Radiological Regulatory Authority\n"
        "  (d) Technology transfer training program (36 months duration)\n"
        "  (e) Manufacturing quality assurance support\n\n"
        "5.2 The Licensor shall respond to technical queries within 10 business days.\n\n"
        "5.3 Technical assistance costs are included in the Annual Technology Support Fee."
    )

    pdf.add_page()
    pdf.heading("Article 8 - Confidentiality", 1)
    pdf.body(
        "8.1 All technical data, drawings, specifications, and know-how provided under "
        "this Agreement constitute Confidential Information.\n\n"
        "8.2 The Licensee shall:\n"
        "  (a) Maintain confidentiality for a period of 20 years from disclosure\n"
        "  (b) Limit access to authorized personnel on a need-to-know basis\n"
        "  (c) Implement physical and cybersecurity measures meeting IAEA NSS-17-T standards\n"
        "  (d) Not disclose to third parties without prior written consent\n\n"
        "8.3 Confidentiality obligations survive termination of this Agreement."
    )

    pdf.add_page()
    pdf.heading("Article 10 - Export Control Compliance", 1)
    pdf.body(
        "10.1 The Licensee acknowledges that the licensed technology is subject to export "
        "control regulations of the Republic of Korea and applicable international regimes.\n\n"
        "10.2 The Licensee shall:\n"
        "  (a) Comply with the Nuclear Suppliers Group (NSG) guidelines\n"
        "  (b) Not re-export or transfer technology to any country not approved in writing\n"
        "  (c) Maintain records of all personnel with access to controlled technology\n"
        "  (d) Implement an Internal Compliance Program (ICP) meeting KINAC standards\n"
        "  (e) Submit annual compliance reports to the Licensor\n\n"
        "10.3 Any violation of export control obligations shall constitute a material breach "
        "entitling the Licensor to immediate termination.\n\n"
        "10.4 The Licensee shall cooperate with any regulatory inspection or audit related "
        "to export control compliance."
    )

    pdf.add_page()
    pdf.heading("Article 12 - Improvements and Enhancements", 1)
    pdf.body(
        "12.1 Any improvements or enhancements to the licensed technology developed by the "
        "Licensor during the term of this Agreement shall be made available to the Licensee.\n\n"
        "12.2 Improvements developed by the Licensee using the licensed technology shall be "
        "owned jointly by both parties.\n\n"
        "12.3 The Licensee shall not file patent applications based on the licensed technology "
        "without prior written consent of the Licensor.\n\n"
        "12.4 Technology improvements shall be subject to the same confidentiality and "
        "export control obligations as the original licensed technology."
    )

    pdf.add_page()
    pdf.heading("Article 15 - Term and Termination", 1)
    pdf.body(
        "15.1 This Agreement shall have an initial term of 40 years from the Effective Date.\n\n"
        "15.2 The Agreement may be renewed for additional 10-year periods by mutual consent.\n\n"
        "15.3 Either Party may terminate this Agreement for material breach if the breach "
        "is not cured within 90 days of written notice.\n\n"
        "15.4 Upon termination, the Licensee shall:\n"
        "  (a) Cease use of all licensed technology (except as needed for plant operation safety)\n"
        "  (b) Return or destroy all confidential documents\n"
        "  (c) Pay all outstanding royalties and fees\n"
        "  (d) Provide certification of compliance within 60 days"
    )

    pdf.output(str(OUT / "Technology_License_Agreement.pdf"))
    print("  [6/8] Technology_License_Agreement.pdf")


# ─────────────────────────────────────────────────────
# PDF 7: NDA Advisory Case History
# ─────────────────────────────────────────────────────
def gen_nda_case_history():
    pdf = DocPDF()
    pdf._doc_title = "NDA Advisory Case History"
    pdf.alias_nb_pages()

    pdf.title_page(
        "NDA Advisory Case History",
        "Compilation of Past NDA Review Cases\nLegal Department - KEPCO E&C",
        "Compiled: December 2024",
    )

    cases = [
        {
            "title": "Case 1: Overly Broad Definition of Confidential Information",
            "original": (
                "Original Clause: 'Confidential Information means any and all information, "
                "whether oral, written, or electronic, disclosed by the Disclosing Party to "
                "the Receiving Party in connection with the Purpose.'"
            ),
            "issue": (
                "Issue Identified: This definition is excessively broad and could encompass "
                "publicly available information, prior knowledge of the Receiving Party, and "
                "independently developed information. This creates unreasonable risk for the "
                "Receiving Party."
            ),
            "recommendation": (
                "Recommended Modification: Add standard exclusions:\n"
                "'Confidential Information does NOT include information that:\n"
                "  (a) is or becomes publicly available through no fault of the Receiving Party;\n"
                "  (b) was known to the Receiving Party before disclosure;\n"
                "  (c) is independently developed by the Receiving Party;\n"
                "  (d) is rightfully received from a third party without restriction.'"
            ),
            "rationale": (
                "Rationale: Standard market practice requires these four exclusions. "
                "Without them, the NDA imposes an unenforceable and commercially unreasonable "
                "burden on the Receiving Party. Reference: ICC Model Confidentiality Agreement (2023)."
            ),
        },
        {
            "title": "Case 2: Missing Regulatory Disclosure Carve-out",
            "original": (
                "Original Clause: 'The Receiving Party shall not disclose any Confidential "
                "Information to any third party whatsoever without the prior written consent "
                "of the Disclosing Party.'"
            ),
            "issue": (
                "Issue Identified: The clause does not permit disclosures required by law, "
                "regulation, or court order. In the nuclear industry, regulatory bodies "
                "(FANR, NRC, NSSC) routinely require disclosure of information for safety reviews."
            ),
            "recommendation": (
                "Recommended Modification: Add regulatory carve-out:\n"
                "'The Receiving Party may disclose Confidential Information to the extent "
                "required by:\n"
                "  (a) applicable law or regulation;\n"
                "  (b) order of a court or governmental authority;\n"
                "  (c) rules of a recognized stock exchange;\n"
                "  (d) nuclear regulatory authority for safety review purposes.\n"
                "The Receiving Party shall provide prompt notice to the Disclosing Party "
                "before such disclosure (unless prohibited by law).'"
            ),
            "rationale": (
                "Rationale: Nuclear industry NDAs must accommodate regulatory disclosure "
                "requirements. Failure to include this carve-out could put the Receiving Party "
                "in a position of either breaching the NDA or violating regulatory requirements."
            ),
        },
        {
            "title": "Case 3: Indefinite Duration",
            "original": (
                "Original Clause: 'The obligations of confidentiality under this Agreement "
                "shall continue indefinitely.'"
            ),
            "issue": (
                "Issue Identified: Indefinite confidentiality obligations are generally "
                "unenforceable in most jurisdictions and create perpetual liability. "
                "Courts in many jurisdictions have struck down indefinite NDA terms."
            ),
            "recommendation": (
                "Recommended Modification: Set a reasonable fixed term:\n"
                "'The obligations of confidentiality shall continue for a period of 5 years "
                "from the date of disclosure of each item of Confidential Information, "
                "except for trade secrets which shall be protected for as long as they "
                "remain trade secrets under applicable law.'"
            ),
            "rationale": (
                "Rationale: Industry standard for commercial NDAs is 3-7 years. "
                "For nuclear technology, 5 years is appropriate for general information, "
                "with trade secret exception for truly proprietary technology. "
                "Reference: AIPN Model NDA, Korean Fair Trade Commission guidelines."
            ),
        },
        {
            "title": "Case 4: No Return of Materials Clause",
            "original": (
                "Original Clause: The NDA contained no provision regarding the return or "
                "destruction of Confidential Information upon termination or request."
            ),
            "issue": (
                "Issue Identified: Without a return-of-materials clause, the Disclosing Party "
                "has no contractual mechanism to require the return or destruction of its "
                "confidential information. This is particularly critical for nuclear technology "
                "where controlled documents must be tracked."
            ),
            "recommendation": (
                "Recommended Modification: Add return/destruction clause:\n"
                "'Upon termination of this Agreement or upon request by the Disclosing Party:\n"
                "  (a) The Receiving Party shall promptly return or destroy all Confidential "
                "Information and copies thereof;\n"
                "  (b) Destruction shall be certified in writing by an authorized officer;\n"
                "  (c) The Receiving Party may retain one archival copy solely for legal "
                "compliance purposes;\n"
                "  (d) Confidential Information in electronic backup systems may be retained "
                "subject to continued confidentiality obligations.'"
            ),
            "rationale": (
                "Rationale: Essential for information security and regulatory compliance. "
                "The archival copy exception is standard practice to allow the Receiving Party "
                "to verify its compliance obligations."
            ),
        },
        {
            "title": "Case 5: Inadequate Remedies Clause",
            "original": (
                "Original Clause: 'In the event of breach, the breaching Party shall pay "
                "damages to the non-breaching Party.'"
            ),
            "issue": (
                "Issue Identified: This generic remedies clause does not acknowledge that "
                "monetary damages may be inadequate for confidentiality breaches, and does "
                "not expressly permit injunctive relief. It also lacks any provision for "
                "liquidated damages or indemnification."
            ),
            "recommendation": (
                "Recommended Modification: Enhance remedies clause:\n"
                "'(a) The Parties acknowledge that breach of this Agreement may cause "
                "irreparable harm for which monetary damages alone would be inadequate.\n"
                "(b) The non-breaching Party shall be entitled to seek injunctive relief "
                "without the need to post bond.\n"
                "(c) The breaching Party shall indemnify and hold harmless the non-breaching "
                "Party against all losses, damages, and expenses arising from the breach.\n"
                "(d) These remedies are cumulative and not exclusive.'"
            ),
            "rationale": (
                "Rationale: Confidentiality breaches in the nuclear sector can cause "
                "irreparable competitive and regulatory harm. Express injunctive relief "
                "provisions are standard in technology-related NDAs."
            ),
        },
    ]

    for case in cases:
        pdf.add_page()
        pdf.heading(case["title"], 1)
        for field in ["original", "issue", "recommendation", "rationale"]:
            pdf.body(case[field])
            pdf.ln(2)

    pdf.output(str(OUT / "NDA_Advisory_CaseHistory.pdf"))
    print("  [7/8] NDA_Advisory_CaseHistory.pdf")


# ─────────────────────────────────────────────────────
# PDF 8: New NDA Draft (with intentional weaknesses)
# ─────────────────────────────────────────────────────
def gen_nda_draft():
    pdf = DocPDF()
    pdf._doc_title = "NDA Draft - Project Gamma"
    pdf.alias_nb_pages()

    pdf.title_page(
        "Non-Disclosure Agreement",
        "Project Gamma - Preliminary Discussion\nBetween KEPCO E&C and GreenField Nuclear Ltd.",
        "Draft Date: February 10, 2025",
    )

    pdf.add_page()
    pdf.heading("1. Definitions", 1)
    pdf.body(
        "1.1 'Confidential Information' means any and all information, whether oral, written, "
        "electronic, or visual, that is disclosed by one Party (the 'Disclosing Party') to "
        "the other Party (the 'Receiving Party') in connection with the Purpose, including "
        "but not limited to technical data, business plans, financial information, customer "
        "lists, trade secrets, and any other information of a proprietary nature.\n\n"
        "1.2 'Purpose' means the evaluation of a potential joint venture for the development "
        "of small modular reactor (SMR) technology."
    )

    pdf.add_page()
    pdf.heading("2. Obligations of Confidentiality", 1)
    pdf.body(
        "2.1 The Receiving Party shall not disclose any Confidential Information to any "
        "third party whatsoever without the prior written consent of the Disclosing Party.\n\n"
        "2.2 The Receiving Party shall use the Confidential Information solely for the Purpose.\n\n"
        "2.3 The Receiving Party shall protect the Confidential Information using the same "
        "degree of care it uses to protect its own confidential information."
    )

    pdf.add_page()
    pdf.heading("3. Term", 1)
    pdf.body(
        "3.1 This Agreement shall be effective from the date of execution.\n\n"
        "3.2 The obligations of confidentiality under this Agreement shall continue indefinitely.\n\n"
        "3.3 Either Party may terminate this Agreement by giving 30 days written notice to "
        "the other Party. Termination shall not affect the confidentiality obligations."
    )

    pdf.add_page()
    pdf.heading("4. Remedies", 1)
    pdf.body(
        "4.1 In the event of breach, the breaching Party shall pay damages to the "
        "non-breaching Party.\n\n"
        "4.2 This Agreement shall be governed by and construed in accordance with the "
        "laws of the Republic of Korea."
    )

    pdf.add_page()
    pdf.heading("5. General Provisions", 1)
    pdf.body(
        "5.1 This Agreement constitutes the entire agreement between the Parties with "
        "respect to the subject matter hereof.\n\n"
        "5.2 This Agreement may not be amended except by a written instrument signed by "
        "both Parties.\n\n"
        "5.3 If any provision is found to be unenforceable, the remaining provisions "
        "shall remain in full force and effect.\n\n"
        "5.4 Neither Party may assign this Agreement without the prior written consent "
        "of the other Party."
    )

    pdf.output(str(OUT / "NDA_Draft_NewProject.pdf"))
    print("  [8/8] NDA_Draft_NewProject.pdf")


# ─────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Generating sample PDFs in {OUT}/...")
    gen_terminology()
    gen_audit_report()
    gen_contracts()
    gen_om_contract()
    gen_license_agreement()
    gen_nda_case_history()
    gen_nda_draft()
    print(f"\nDone! {len(list(OUT.glob('*.pdf')))} PDFs generated.")
