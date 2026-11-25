---
title: Industry guide
kind: appendix
summary: Per-industry KPIs, cross-fact Pages, data-protection notes and extension ideas, plus how to add a new industry pack.
read_when: You are choosing, adapting or authoring an industry pack.
---
# Appendix B - Industry guide

Packs live in `industries/`. Each is a *starting point*: rename, localize synonyms, and extend. Coverage was chosen for the verticals that data/AI delivery teams
meet most often (BFSI, retail/CPG, manufacturing, healthcare/life sciences) plus common adjacent ones (telecom, energy/utilities, supply chain, education).

For every industry: the KPIs the pack models, the **cross-fact KPIs that need a Page**, data-protection notes, questions that sell the demo, and how to extend.

## Retail (`retail.yaml`)
- Models: sales, returns, inventory; store, customer, product, date. Measures: revenue, units, orders, AOV, return count/amount, stock, low-stock snapshots.
- Page-worthy: **Return rate** (returns / revenue), **Total revenue** (gross definition).
- Watch: *store region vs customer region* ambiguity; returns have no store. Instruct the agent which to use.
- Demo questions: revenue by category last quarter; return rate this year vs last; region with high revenue but high returns.
- Extend: basket analysis, promotions (see CPG), loyalty tiers (enriched customer view with NTILE).

## CPG / FMCG (`cpg_fmcg.yaml`)
- Models: secondary sales (gross, discount, net), promotions, retailer/channel, shelf audits. Measures: net sales, gross sales, trade spend and rate, units, out-of-stock rate, facings.
- Page-worthy: **Net sales / gross-to-net**, **Out-of-stock rate**; promo lift (agent instruction: compare promoted vs "No Promotion" slices).
- Extend: distribution (numeric/weighted), price-pack architecture, sell-in vs sell-out reconciliation (needs both facts: Page).

## Banking (`bfsi_banking.yaml`)
- Models: customers, deposit/card accounts, loans, transactions, loan snapshots. Measures: transaction count/value, fraud rate, outstanding balance, NPA balance/ratio, days past due.
- Page-worthy: **NPA ratio** (point-in-time: state the snapshot date), **Fraud rate** (by count, not value).
- Data protection: PCI-DSS (never card PANs), GLBA/privacy laws, AML/KYC retention. Aggregate to segment/region; never output names.
- Extend: LCR/NSFR liquidity, ECL staging, cross-sell propensity (enriched view), complaint analytics.

## Insurance (`bfsi_insurance.yaml`)
- Models: policies (written premium, sum insured), claims (claimed, paid, status, cause). Measures: written premium, policy count, average premium, claim count, paid amount, rejection rate.
- Page-worthy: **Loss ratio** (paid claims / premium; state paid vs incurred, written vs earned) - a textbook cross-fact KPI; **Written premium** (not earned).
- Extend: earned premium (needs exposure periods), reserves, combined ratio, fraud scoring, telematics (usage-based).

## Healthcare provider (`hls_provider.yaml`)
- Models: encounters (type, diagnosis, LOS, charges, readmission), billing (billed, allowed, denial). Measures: encounters, unique patients, ALOS, 30-day readmission rate, collection rate, denial rate.
- Page-worthy: **30-day readmission rate** (filter to inpatient for benchmarks), **Collection rate**.
- Data protection: HIPAA/GDPR special categories. Demo data is synthetic. Agent instructions suppress small cells (< 11) and forbid names. For real data use masks/policies (user's decision).
- Extend: FHIR/OMOP mappings (see public repos), quality measures (HEDIS), bed occupancy, OR utilization.

## Pharma / life sciences (`hls_pharma_lifesciences.yaml`)
- Models: trial enrollment, adverse events, prescription sales; trial, site, product, prescriber. Measures: enrolled, screen failures/rate, dropouts, AE counts, serious AE share, net sales, active prescribers.
- Page-worthy: **Screen failure rate**, **Serious AE share** (event-based; screening signal, not causality).
- Data protection: GxP, HIPAA/GDPR, pharmacovigilance reporting rules. Counts of events are not counts of patients - say so in instructions.
- Extend: site performance scoring, trial supply, market access, MedTech devices (installed base, service events).

## Manufacturing (`manufacturing.yaml`)
- Models: production by line/shift (planned, downtime, ideal, produced, scrapped), downtime events. Measures: units, scrap rate, availability, performance, quality, **OEE** (single measure as the product of three ratios on summed values).
- Page-worthy: **OEE** (never average OEE percentages), **Scrap rate**. Production minutes and recorded stoppages come from different sources: instruct the agent to say which it used.
- Evidence: an earlier builder revision's OEE measure equalled an independent recomputation (see [appendix G](G-verification-evidence.md)).
- Extend: maintenance (MTBF/MTTR), energy per unit, supplier quality, traceability, sensor time series.

## Telecom (`telecom.yaml`)
- Models: usage + revenue, network quality, churn events. Measures: usage revenue, active subscribers, **ARPU**, data volume, call drop rate, latency, churned subscribers.
- Page-worthy: **ARPU** (active-subscriber based), **Churn rate** (churned / base: cross-source).
- Data protection: subscriber privacy, lawful-intercept boundaries; aggregate to segment/region.
- Extend: network capacity, handset mix, offer response, fraud (see public telco fraud accelerator).

## Energy and utilities (`energy_utilities.yaml`)
- Models: meter consumption/billing, grid outages. Measures: kWh, peak share, billed amount, average rate, outage count, customer minutes interrupted, average duration.
- Page-worthy: **SAIDI** (customer-minutes / customers served; the base is `customers_served` on `dim_asset` for Feeder assets, so it spans two sources and is an approximation), **Peak share**.
- Extend: SAIFI/CAIDI, demand response, renewables, asset health, forecasting (public accelerators).

## Supply chain and logistics (`supply_chain_logistics.yaml`)
- Models: shipments (cost, planned vs actual days, on-time), inventory positions (on hand, backorders, reorder point). Measures: shipments, on-time rate, freight cost, cost per kg, transit days, below-reorder rate.
- Page-worthy: **On-time delivery rate** (by shipment count), **Below reorder point rate** (snapshot-based).
- Extend: OTIF (needs order lines), supplier scorecards, network optimization (public routing/optimization accelerators).

## Education (`education.yaml`)
- Models: enrollments with grade points and drop flag, tuition invoices. Measures: enrollments, unique students, GPA, pass rate, drop rate, invoiced/paid/outstanding, collection rate.
- Page-worthy: **Pass rate** (completed enrollments only), **Collection rate**.
- Data protection: FERPA/GDPR. No protected attributes modeled; forbid ranking individuals by scholarship; suppress small groups.
- Extend: retention/cohort survival, advising risk flags (governed carefully), course demand planning.

## Adding a new industry (30-60 min)
1. Copy `templates/spec_template.yaml`. 2. Write 3-5 domains. 3. Model 3-5 dimensions and 2-3 facts with a grain sentence each; use `lookup`/`derived` for consistency and a skewed generator for tail events.
4. Two metric views (3-6 measures each, synonyms in business language). 5. One Page per cross-fact KPI. 6. Agent instructions with each formula and a privacy line.
7. `validate` (0/0) and `check`; optionally build once on a throwaway schema and verify `MEASURE()` against SQL (only that earns status `Live`, recorded in [appendix G](G-verification-evidence.md)); open a PR with the pack as `Local only` (CONTRIBUTING.md in the repository root, not part of the installed skill, lists the doc steps).
