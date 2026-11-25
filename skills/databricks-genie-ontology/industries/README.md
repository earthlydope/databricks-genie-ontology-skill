---
title: Industry packs
kind: catalog
summary: The 11 industry packs with their domains, metric views, cross-fact Pages and the canonical live-verification status of each.
read_when: You are choosing a pack or need to know how far a pack has been proven.
---
# Industry packs

Each file is a complete spec for `scripts/genie_onto.py` (synthetic data, tables, metric views, domains, a Genie agent, Pages).
Every pack passes `validate` (0 errors, 0 warnings) and `check` (integrity and ratio-realism checks); tests pin realistic behaviour of the headline ratios per pack. Date-ordering gaps in some packs are known (see appendix F).
**Status** (canonical; evidence and dates in [appendix G](../appendix/G-verification-evidence.md)): `Live 1.0.0` = built on a real workspace with builder 1.0.0 (0 errors, all audits PASS, `MEASURE()` correct);
`Live earlier` = built live with a pre-release revision; `Local only` = same code paths, local checks only. Builder 1.1.0 changed validation and guards, not generated SQL, and was not re-run live.
Build any pack on a throwaway schema first. Known data-realism gaps: [appendix F](../appendix/F-known-limitations.md).

| Pack | Status | Domains | Metric views | Cross-fact Pages |
|---|---|---|---|---|
| `retail.yaml` | Live 1.0.0 | Sales, Customer, Supply Chain, Finance | sales performance, customer returns, inventory health | Customer Return Rate |
| `cpg_fmcg.yaml` | Local only | Sales, Trade Marketing, Supply | secondary sales, shelf availability | (Net Sales, OOS definitions) |
| `bfsi_banking.yaml` | Live earlier | Customer, Payments, Lending, Risk and Fraud | transaction activity, loan portfolio | NPA Ratio, Fraud Rate (definitions; point-in-time caveat) |
| `bfsi_insurance.yaml` | Local only | Underwriting, Claims, Customer, Finance | premium performance, claims performance | Loss Ratio |
| `hls_provider.yaml` | Live 1.0.0 | Clinical, Revenue Cycle, Patient | clinical operations, revenue cycle | Readmission rate, Collection rate |
| `hls_pharma_lifesciences.yaml` | Local only | Clinical Development, Safety, Commercial | trial enrollment, safety signals, commercial performance | Screen Failure Rate, Serious AE Share |
| `manufacturing.yaml` | Live earlier | Production, Quality, Maintenance | production performance (OEE), downtime analysis | OEE |
| `telecom.yaml` | Live 1.0.0 | Revenue, Network, Customer | revenue/usage, network quality, churn events | Churn Rate, ARPU |
| `energy_utilities.yaml` | Local only | Customer Energy, Grid Reliability, Finance | energy consumption, grid reliability | SAIDI |
| `supply_chain_logistics.yaml` | Local only | Transportation, Warehousing, Procurement | logistics performance, inventory positions | On-Time Delivery, Below Reorder Rate |
| `education.yaml` | Local only | Academics, Student Success, Finance | academic performance, tuition collections | Pass Rate, Collection Rate |

Use: `cp industries/<pack>.yaml my_spec.yaml`, edit catalog/schema/names, then follow [SKILL.md](../SKILL.md). Authoring a new pack: [spec format](../references/03-spec-format.md) and [industry guide](../appendix/B-industry-guide.md#adding-a-new-industry-30-60-min).
Packs contain no real data. Brand/product/person names are generated placeholders.
