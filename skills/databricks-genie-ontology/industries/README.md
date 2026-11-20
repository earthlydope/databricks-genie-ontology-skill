# Industry packs

Each file is a complete spec for `scripts/genie_onto.py` (synthetic data, tables, metric views, domains, a Genie agent, Pages).
All eleven pass `validate` (0 errors, 0 warnings) and `check` (integrity + realism checks), and a test suite pins realistic behaviour per pack.
Built live on Databricks with the **final** builder: **retail**, **telecom**, **hls_provider** (0 errors, all audits PASS, `MEASURE()` correct). Built live with an earlier builder revision: **bfsi_banking**, **manufacturing**.
Not yet built live: **cpg_fmcg, bfsi_insurance, hls_pharma_lifesciences, energy_utilities, supply_chain_logistics, education** (same code paths, local checks only). Build any pack on a throwaway schema first. The retail Genie agent was exercised through conversation in an earlier hand-built version of the same idea.

| Pack | Domains | Metric views | Cross-fact Pages |
|---|---|---|---|
| `retail.yaml` | Sales, Customer, Supply Chain, Finance | sales performance, customer returns, inventory health | Customer Return Rate |
| `cpg_fmcg.yaml` | Sales, Trade Marketing, Supply | secondary sales, shelf availability | (Net Sales, OOS definitions) |
| `bfsi_banking.yaml` | Customer, Payments, Lending, Risk and Fraud | transaction activity, loan portfolio | NPA Ratio, Fraud Rate (definitions; point-in-time caveat) |
| `bfsi_insurance.yaml` | Underwriting, Claims, Customer, Finance | premium performance, claims performance | Loss Ratio |
| `hls_provider.yaml` | Clinical, Revenue Cycle, Patient | clinical operations, revenue cycle | Readmission rate, Collection rate |
| `hls_pharma_lifesciences.yaml` | Clinical Development, Safety, Commercial | trial enrollment, safety signals, commercial performance | Screen Failure Rate, Serious AE Share |
| `manufacturing.yaml` | Production, Quality, Maintenance | production performance (OEE), downtime analysis | OEE |
| `telecom.yaml` | Revenue, Network, Customer | revenue/usage, network quality, churn events | Churn Rate, ARPU |
| `energy_utilities.yaml` | Customer Energy, Grid Reliability, Finance | energy consumption, grid reliability | SAIDI |
| `supply_chain_logistics.yaml` | Transportation, Warehousing, Procurement | logistics performance, inventory positions | On-Time Delivery, Below Reorder Rate |
| `education.yaml` | Academics, Student Success, Finance | academic performance, tuition collections | Pass Rate, Collection Rate |

Use: `cp industries/<pack>.yaml my_spec.yaml`, edit catalog/schema/names, then follow `../SKILL.md`. Authoring a new pack: `../references/03-spec-format.md` and `../references/11-industry-guide.md`.
Packs contain no real data. Brand/product/person names are generated placeholders.
