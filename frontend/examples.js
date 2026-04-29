// ── Pre-loaded example data for each tool ───────────────────────────────────

/* eslint-disable no-unused-vars */
// Exposed as window.EXAMPLES for use in app.js loadExample()
const EXAMPLES = window.EXAMPLES = {

  process: {
    'invoice': {
      text: `INVOICE #INV-2026-0391

From: Nordic Data Solutions ApS
To: GreenField Manufacturing A/S

Invoice Date: 2026-04-01
Due Date: 2026-04-30
Payment Terms: Net 30

Description of services:
AI-powered document processing system for automating invoice intake and ERP data entry.
Project delivered in three phases over Q1 2026.

| Service | Hours | Rate | Amount |
|---------|-------|------|--------|
| Solution Architecture | 24 | 1,500 DKK | 36,000 DKK |
| AI Development | 120 | 1,200 DKK | 144,000 DKK |
| Integration & Testing | 40 | 1,000 DKK | 40,000 DKK |
| Project Management | 16 | 1,400 DKK | 22,400 DKK |

Subtotal: 242,400 DKK
VAT (25%): 60,600 DKK
Total: 303,000 DKK

Bank: Nordea
Account: 2211-0098765432
SWIFT: NDEADKKK
Reference: INV-2026-0391

Contact: billing@nordicdata.dk`,
      document_type: 'invoice',
    },

    'contract': {
      text: `SERVICE AGREEMENT

Agreement Number: SA-2026-0174
Effective Date: 2026-05-01
Duration: 12 months (auto-renewal)

PARTIES:
- Provider: DataFlow Consulting A/S, CVR 31458902, Aarhus
- Client: Meridian Logistics A/S, CVR 28193746, Copenhagen

SCOPE OF SERVICES:
DataFlow Consulting will provide ongoing AI automation services including:
1. Maintenance of document processing pipelines
2. Monthly optimization of extraction models
3. 24/7 monitoring and incident response
4. Quarterly business review and roadmap planning

COMPENSATION:
Monthly retainer: 85,000 DKK (ex. VAT)
Additional development: 1,200 DKK/hour
Payment terms: Net 15

TERMINATION:
Either party may terminate with 90 days written notice.
Early termination fee: 3 months retainer.

Governing Law: Danish law
Dispute Resolution: Copenhagen Arbitration

Signed: Erik Hansen, CEO DataFlow Consulting A/S
Date: 2026-04-15
Contact: legal@dataflow.dk`,
      document_type: 'contract',
    },

    'meeting': {
      text: `MEETING NOTES — AI Platform Sprint Review

Date: 2026-04-14
Time: 10:00-11:30
Location: Conference Room B, Aarhus Office
Attendees: Simon M. (Dev), Anna K. (Data), Lars P. (DevOps), Mette S. (PM)

AGENDA:
1. Sprint 12 demo and review
2. Pipeline performance metrics
3. Q2 roadmap discussion

KEY DECISIONS:
- Approved migration of document processing to Azure Container Apps
- Agreed to add support for PDF input (not just plain text)
- Budget approved for Claude API usage in production (est. 4,000 DKK/month)

ACTION ITEMS:
- Simon: Implement PDF text extraction using PyMuPDF — deadline 2026-04-21
- Anna: Set up monitoring dashboard for pipeline throughput — deadline 2026-04-18
- Lars: Configure auto-scaling for container instances — deadline 2026-04-25
- Mette: Schedule customer demo for GreenField Manufacturing — deadline 2026-04-16

METRICS:
- Pipeline throughput: 340 documents/hour (up from 210)
- Extraction accuracy: 94.2% (target: 95%)
- Average processing time: 2.3 seconds per document

Next Meeting: 2026-04-28, 10:00`,
      document_type: 'meeting_notes',
    },
  },

  analyze: {
    'job': {
      text: `AI & Automation Intern — Columbus

Are you passionate about AI, automation, cloud technologies, or building smart tools that solve real business problems?

As an AI & Automation Intern at Columbus, you'll join a cross-functional AI project group working across our two Business Lines: M3 (ERP) and Data & AI. You will design, test, and build AI-powered prototypes and automations that streamline internal workflows or add new value to our ERP customers.

Location: Aarhus
Duration: Aug/Sep - Dec 2026 · Full-time
Contact: Louise.Scheibner@columbusglobal.com

Requirements:
- Python or TypeScript/JavaScript
- Cloud code or app development
- Interest in AI and automation

About Columbus:
Columbus A/S is a global digital consultancy with over 1,500 colleagues across more than 10 countries. Founded in 1989. Visit https://www.columbusglobal.com for more.`,
      focus: 'organizational',
    },

    'email': {
      text: `From: anders.jensen@techcorp.dk
To: maria.nielsen@clientco.dk
Subject: Q3 2026 Project Update

Hi Maria,

I wanted to follow up on our meeting from 2026-04-15 regarding the data migration project.

Key updates:
- Phase 1 completed on schedule (budget: 450,000 DKK)
- Phase 2 kickoff planned for 2026-05-01
- New team member: Sara Pedersen joining from TechCorp A/S

Please review the attached timeline and let me know if the 2026-06-30 deadline still works for your team.

You can also check the project dashboard at https://projects.techcorp.dk/q3-migration

Best regards,
Anders Jensen
Senior Consultant, TechCorp A/S`,
      focus: 'general',
    },

    'report': {
      text: `# Infrastructure Modernization Report

## Executive Summary

This report outlines the planned migration of legacy systems to cloud-native architecture for Northwind Traders ApS.

## Current State

The existing infrastructure runs on on-premises servers with the following stack:
- 3x physical database servers (PostgreSQL 12)
- 2x application servers (Java 11, Tomcat 9)
- 1x file storage server (Windows Server 2019)

Total monthly cost: 85,000 DKK
Uptime SLA: 99.2% (target: 99.9%)

## Proposed Architecture

| Component | Current | Proposed |
|-----------|---------|----------|
| Database | On-prem PostgreSQL | Azure Database for PostgreSQL |
| Application | Tomcat on VM | Azure Container Apps |
| Storage | Windows file server | Azure Blob Storage |
| CI/CD | Manual deployment | GitHub Actions + Azure DevOps |

## Timeline

- Phase 1 (2026-Q3): Database migration
- Phase 2 (2026-Q4): Application containerization
- Phase 3 (2027-Q1): Storage migration and cutover

Contact: infrastructure@northwind.dk
Project lead: Erik Hansen, Northwind Traders ApS`,
      focus: 'technical',
    },
  },

  extract: {
    'invoice': {
      text: `INVOICE #INV-2026-0847

From: DataFlow Solutions ApS
To: Meridian Logistics A/S

Invoice Date: 2026-04-10
Due Date: 2026-05-10
Payment Terms: Net 30

| Service | Hours | Rate | Amount |
|---------|-------|------|--------|
| AI Consulting | 40 | 1,200 DKK | 48,000 DKK |
| Development | 80 | 950 DKK | 76,000 DKK |
| Testing & QA | 20 | 800 DKK | 16,000 DKK |

Subtotal: 140,000 DKK
VAT (25%): 35,000 DKK
Total: 175,000 DKK

Bank: Danske Bank
Account: 3210-0012345678
Reference: INV-2026-0847`,
      fields: 'Invoice Date, Due Date, Subtotal, VAT, Total, From, To, Reference',
      strategy: 'auto',
    },

    'contact': {
      text: `Name: Louise Scheibner
Title: Hiring Manager
Company: Columbus A/S
Department: M3 Business Line
Email: Louise.Scheibner@columbusglobal.com
Location: Aarhus, Denmark
Phone: +45 7020 5000`,
      fields: 'Name, Title, Company, Email, Location, Phone',
      strategy: 'key_value',
    },

    'table': {
      text: `Team allocation for Q3 2026:

| Name | Role | Project | Allocation |
|------|------|---------|------------|
| Simon M. | AI Developer | Agent Platform | 100% |
| Anna K. | Data Engineer | ETL Pipeline | 80% |
| Lars P. | DevOps | Infrastructure | 60% |
| Mette S. | PM | Cross-team | 50% |`,
      fields: 'Name, Role, Project, Allocation',
      strategy: 'table',
    },
  },

  summarize: {
    'business': {
      text: `Columbus is a global digital consultancy with a local presence, helping businesses transform and thrive through technology, data, and human insight. With over 1,500 colleagues across more than 10 countries, they bring global perspectives and local understanding. The company was founded in 1989 and has since grown to become a leading player in ERP implementation, data analytics, and digital commerce solutions.

The Navigator Internship Program at Columbus offers students a unique opportunity to work on real business cases alongside senior consultants and AI engineers. Interns work on cross-functional teams spanning the M3 (ERP) and Data & AI business lines. The program is designed to give hands-on experience with modern AI and cloud technologies while building a professional network.

Recent initiatives include the development of AI-powered tools for internal consultant workflows, automation of data processing pipelines for ERP customers, and experimentation with large language models for document analysis and report generation. The company emphasizes a culture of trust, collaboration, and curiosity, with clear career paths and development support for all employees.

Columbus operates primarily in the Nordics, with offices in Aarhus, Copenhagen, Middelfart, Aalborg, and Viborg in Denmark alone. They also have significant presence in the UK, Norway, Sweden, and India. The company's technology stack includes Microsoft Dynamics 365, Infor M3, Azure cloud services, and increasingly Python and TypeScript for AI and automation workloads.`,
      format: 'bullets',
      max_points: 5,
    },

    'technical': {
      text: `The ReAct (Reasoning + Acting) pattern is a framework for building AI agents that can reason about tasks and take actions to accomplish them. Unlike simple prompt-response systems, a ReAct agent maintains a loop where it thinks about what to do next, selects and executes a tool, observes the result, and then decides whether to continue or provide a final answer.

In our implementation, the agent uses Claude's tool calling capability to decide which tools to use and how to parameterize them. The available tools include document analysis (type detection, entity extraction, key point identification), data extraction (key-value, table, and list strategies), text summarization (AI-powered with extractive fallback), and data pipeline execution (TypeScript automation workflows).

The pipeline component is built in TypeScript with full type safety via Zod runtime validation. It implements a composable step-chaining architecture where each transformation (clean, filter, map, aggregate, format) is an independent function that can be composed into arbitrary workflows. The API connector includes retry logic with exponential backoff for resilient data fetching.

Error handling is a key design consideration. The agent implements retry with exponential backoff for rate limits and server errors. Tool execution failures return structured error objects rather than crashing. The pipeline uses a custom PipelineError class that preserves the failing step name and original error for debugging. All components are covered by automated tests running in GitHub Actions CI.`,
      format: 'bullets',
      max_points: 4,
    },

    'article': {
      text: `Denmark is rapidly emerging as a hub for artificial intelligence innovation in Europe. The country's combination of strong technical universities, progressive government policies, and a thriving startup ecosystem has created fertile ground for AI development. Copenhagen and Aarhus in particular have seen significant growth in AI-focused companies and research institutions.

Major Danish companies like Novo Nordisk, Maersk, and Vestas are investing heavily in AI capabilities, while consultancies such as Columbus, Netcompany, and Systematic are building dedicated AI practices to serve enterprise clients. The Danish government's AI strategy, launched in 2019 and updated in 2024, emphasizes responsible AI development with a focus on healthcare, energy, and public sector applications.

The education sector has responded with new AI-focused programs at DTU, Aarhus University, and the IT University of Copenhagen. These programs combine theoretical foundations in machine learning and data science with practical experience through industry partnerships and internship programs. Several companies now offer structured internship programs specifically targeting AI and automation skills.

One notable trend is the growing adoption of large language models and automation tools in traditional industries. ERP vendors and system integrators are experimenting with AI-powered document processing, automated testing, and intelligent workflow orchestration. This convergence of enterprise software and AI creates significant demand for developers who understand both domains.`,
      format: 'paragraph',
      max_points: 5,
    },
  },
};

// Dead code removed: DEMO_MAP, loadDemo, switchToTool, duplicate loadExample
// The active loadExample() lives in app.js
