# SolarQC — AI-Powered Solar Sales Quality Control

![SolarQC Tests](https://github.com/leonardo-luis-medina/AI.AGENT.SLR/actions/workflows/tests.yml/badge.svg)


# ☀️ SolarQC
### AI-Powered Solar Sales Quality Control Agent

![SolarQC Tests](https://github.com/leonardo-luis-medina/AI.AGENT.SLR/actions/workflows/tests.yml/badge.svg)

**SolarQC** is an AI-assisted quality control application designed to evaluate fictional Australian solar sales transactions against structured business policies.

It combines deterministic validation, locally hosted language-model analysis, automated monitoring, and an interactive web dashboard.

The project demonstrates how AI-assisted workflows can support operational quality assurance while maintaining structured decision-making and human review.

## 🚀 Live Demo

**Try SolarQC:** https://ai-agent-solar.streamlit.app/

The public demonstration allows visitors to evaluate fictional solar sales transactions using nine deterministic quality control rules.

No installation, API key, or locally running AI model is required.

> **Note:** The public demo uses deterministic QC. The full local application supports two additional LLM-assisted checks using Ollama.

## ✨ Key Features

- **11 Quality Control Rules:** Nine deterministic checks and two AI-assisted checks.
- **AI-Assisted Analysis:** Uses Qwen 2.5 through Ollama for local language-model analysis.
- **Interactive Dashboard:** Submit fictional solar sales deals and inspect rule-level findings.
- **Automated Monitoring:** Detects changes in connected Google Sheets records and triggers reevaluation.
- **CRM Integration:** Supports HubSpot deal retrieval and controlled writeback workflows.
- **Policy References:** Associates QC findings with corresponding policy information.
- **Human Review:** Supports NEEDS_HUMAN outcomes for cases requiring additional assessment.
- **Evaluation Framework:** Includes labeled evaluation cases and automated testing.
- **CI/CD:** Uses GitHub Actions for automated regression testing.
- **Public Demonstration:** Cloud-hosted deterministic QC without requiring a local AI model.

## 🧠 How SolarQC Works

```text
                SOLAR SALES DEAL
                       |
                       v
                DATA VALIDATION
                       |
                       v
                 QC ORCHESTRATOR
                       |
             +---------+---------+
             |                   |
             v                   v
       DETERMINISTIC        AI-ASSISTED
       RULES R01-R09        RULES R10-R11
             |                   |
             |              Qwen 2.5
             |              via Ollama
             |                   |
             +---------+---------+
                       |
                       v
                 QC DECISION
                       |
           +-----------+-----------+
           |           |           |
          PASS        FAIL     NEEDS_HUMAN
                       |
                       v
                 DASHBOARD
```

The system uses deterministic rules for structured checks and language-model assistance for selected qualitative assessments.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | API endpoints |
| Streamlit | Interactive web dashboard |
| Ollama | Local LLM execution |
| Qwen 2.5 3B | Pretrained language model |
| Google Sheets API | Spreadsheet integration |
| HubSpot API | CRM integration |
| Pytest | Automated testing |
| GitHub Actions | Continuous integration |
| Streamlit Community Cloud | Public demo hosting |

## 🧪 Try the Demo

1. Open the [SolarQC Live Demo](https://ai-agent-solar.streamlit.app/).
2. Select **Interactive QC**.
3. Choose a fictional sample deal.
4. Review or modify its details.
5. Click **Run Quality Check**.
6. Review the overall QC decision and individual rule findings.

### Example Results

| Sample | Expected Result |
|---|---|
| Complete Sale | PASS |
| Missing Requirements | FAIL |
| Unverified Roof Type | FAIL |

The public demo evaluates nine deterministic rules. The local full-AI workflow supports all eleven.

## 📊 Testing

SolarQC includes automated tests covering QC execution, integrations, validation, evaluation, and dashboard-supporting functionality.

Run the test suite:

```bash
python -m pytest -q
```

The project previously passed 217 automated tests. Additional public-demo tests were introduced afterward.

Current test status is tracked through the GitHub Actions badge above.

## 🔒 Security and Scope

SolarQC is a portfolio demonstration.

- All public sample deals are fictional.
- Public mode disables full local-AI execution.
- Public visitors cannot initiate HubSpot or Google Sheets operations through the dashboard.
- Local credentials should be stored outside version control.
- Results are illustrative and are not regulatory certifications or installation approvals.

## ⚙️ Local Development

Clone the repository:

```bash
git clone https://github.com/leonardo-luis-medina/AI.AGENT.SLR.git
cd AI.AGENT.SLR
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it.

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch the dashboard:

```bash
python -m streamlit run dashboard/app.py
```

The deterministic demonstration works without a local LLM.

Full AI functionality requires a separately configured Ollama environment and the appropriate local model.

## 🗺️ Project Roadmap

- [x] Core quality control engine
- [x] Deterministic validation rules
- [x] LLM-assisted checks
- [x] Google Sheets integration
- [x] HubSpot integration
- [x] Change detection and monitoring
- [x] Interactive Streamlit dashboard
- [x] Automated testing and CI/CD
- [x] Public deterministic QC deployment
- [ ] Final security and deployment verification
- [ ] Portfolio screenshots and documentation polish

## ⚠️ Disclaimer

SolarQC is an independent portfolio project developed for educational and demonstration purposes.

Its policies, records, and sample scenarios are illustrative. It is not a substitute for professional, technical, legal, or regulatory review.