---
title: Public repositories and docs
kind: appendix
summary: Verified links to official Databricks docs, the example this skill generalizes, and public semantics/Genie/governance repos with licence notes.
read_when: You want prior art, accelerators or official documentation.
---
# Appendix A - Public repositories and docs

Links are **referenced, not copied**. Verified to exist and not be archived on 2026-11-20 with `scripts/verify_links.py`; star counts and licenses change. Many Databricks
repos use the Databricks License (source-available, not OSI open source): read each license before reusing code. Repos marked **†** publish **no license file**: by default that means all rights reserved, so read them but do not copy from them.
Treat community repos as examples to read, not dependencies.

## Official docs (starting points)
- Unity Catalog business semantics overview: https://docs.databricks.com/aws/en/business-semantics/
- Genie spaces and agents: https://docs.databricks.com/aws/en/genie/
- Data quality monitoring: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring
- Metric views: https://docs.databricks.com/aws/en/uc-semantics/metric-views/
- Domains: https://docs.databricks.com/aws/en/uc-semantics/domains
- Pages: https://docs.databricks.com/aws/en/uc-semantics/pages
- Certify / deprecate data: https://docs.databricks.com/aws/en/data-governance/unity-catalog/certify-deprecate-data
- Genie One chat: https://docs.databricks.com/aws/en/genie-one/chat
- Data classification (feeds masking tools): https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-classification

## The example this skill generalizes
- https://github.com/databeli/genie_ontology † - "Northwind Retail" Genie Ontology demo (notebooks + README + walkthrough video; no license published †). The retail pack is a spec-driven re-authoring of the same star-schema idea; credit to the author.
- https://github.com/databeli/databricks_course † - course notebooks incl. `15_Metric_Views`.
- https://www.databricks.com/blog/how-partners-use-genies-free-tier-azure-databricks - partner walkthrough of using Genie on a free tier.

## Semantics, Genie and governance tooling (Databricks field + community)
| Repo | What it gives you |
|---|---|
| https://github.com/databricks-solutions/uc-semantics-patterns | Tested metric-view patterns: time intelligence, semi-additive, ranking, currency, segmentation, fiscal/retail calendars, ABC classification |
| https://github.com/databricks-solutions/genie-ontology-readiness | Databricks App that scores workspace readiness across UC, metadata, relationships, metrics, agents, domains, adoption; frames GA vs learned layer |
| https://github.com/databricks-solutions/databricks-genie-workbench | Create, score and optimize Genie spaces |
| https://github.com/databricks-solutions/genie-best-practices-agent | Evaluates a Genie space configuration and the UC data behind it |
| https://github.com/databricks-solutions/genierails | Govern and ship Genie agents as code (classification -> masks -> access rules, dev-to-prod) |
| https://github.com/databricks-solutions/uc-declarative-abac | Declarative attribute-based access control for Unity Catalog |
| https://github.com/databricks-solutions/genie-code-skills-demo | Example Genie Code skills, instructions and MCP setup |
| https://github.com/databricks-solutions/ai-dev-kit | Toolkit and skills for coding agents on Databricks |
| https://github.com/databricks-solutions/aibi-genie-enablement-lab | AI/BI Genie enablement lab |
| https://github.com/databrickslabs/dqx | Data-quality rules and checks for PySpark DataFrames and tables |
| https://github.com/databricks-demos/dbdemos | Installable Databricks demos (many industries) |
| https://github.com/databricks/databricks-sdk-py | Python SDK (REST automation when a token is available) |
| https://github.com/epeyman/retail-ontology-databricks | Generic retail ontology bound to UC metric views |
| https://github.com/DevDataAnalyst/OntologyStudio | Turn UC tables into an editable ontology and metric views |
| https://github.com/CheeYuTan/trusted-context-databricks † | Metric-view tutorial: LOD, window semantics, agent metadata |
| https://github.com/sunnysingh-db/ai-genie-space-generator † | Generates metric views and a Genie space from data using AI |
| https://github.com/barath2904/uc-metric-views | Generate, validate and deploy metric views |
| https://github.com/mkahn5/lattice † | Visual intelligence/ontology view of a workspace |

## Healthcare and life sciences (HLS)
- https://github.com/databricks-industry-solutions/pixels - medical imaging at scale
- https://github.com/databricks-industry-solutions/omop-cdm - OMOP common data model on the lakehouse
- https://github.com/databricks-industry-solutions/interop - FHIR ingestion to patient outcomes
- https://github.com/databricks-industry-solutions/smart-claims - claims management (also relevant to insurance)
- https://github.com/databricks-industry-solutions/vital-skills - HLS agent skills for Genie Code (genomics, RWE cohorts...)
- https://github.com/mkhomutskyi/synthea-healthcare-genie-demo - Genie demo with synthetic healthcare data and a governed metric view
- https://github.com/philsalm/mvp-metric-views-workshop † - metric-views workshop on synthetic HEDIS quality data
- https://github.com/teo-ma/Clinical-Demo-Genie † - clinical-trials Genie demo
- https://github.com/Le4ndroGomes/hsl-dbx-agents † - hospital data sessions (medallion, metric view, pages)

## Banking, financial services and insurance (BFSI)
- https://github.com/databricks-industry-solutions/banking-agent-accelerator
- https://github.com/databricks-industry-solutions/value-at-risk - risk back-testing
- https://github.com/databricks-industry-solutions/merchant-classification
- https://github.com/databricks-industry-solutions/esg-scoring
- https://github.com/zhihantan/smbc-apac-genie † - synthetic customer 360 with curated Genie agents
- https://github.com/jgraham0325/genie_banking_example † - simple banking Genie space
- https://github.com/ChrisMoon-DB/databricks-fraud-triage-agent † - fraud triage with Genie and a Databricks App
- https://github.com/patrick-chan-cfa/insurance-genie-ontology † - Genie Ontology for insurance
- https://github.com/viralmdesai/genie-ontology-insurance † - insurer loss-ratio worked example
- https://github.com/sas2106-data/axa-ontology-app - ontology explorer app for an insurance domain
- https://github.com/databricks-solutions/regulatory_data_governance - regulatory data governance

## Manufacturing
- https://github.com/archana986/manufacturing-genie-workshop - Genie workshop (OEE, quality, downtime)
- https://github.com/databricks-industry-solutions/factory-optimization - OEE end to end
- https://github.com/databricks-industry-solutions/digital-twin - IoT digital twins
- https://github.com/databricks-industry-solutions/manufacturing-root-cause-analysis
- https://github.com/livingdw67/cmapss-predictive-maintenance - predictive maintenance on a governed semantic layer
- https://github.com/skyler-myers-db/ai-bi-genie-poc † - AI/BI Genie PoC for manufacturing sales

## Retail and CPG
- https://github.com/databricks-industry-solutions/many-model-forecasting
- https://github.com/databricks-industry-solutions/fine-grained-demand-forecasting
- https://github.com/databricks-industry-solutions/customer-lifetime-value
- https://github.com/databricks-industry-solutions/segmentation
- https://github.com/Moratuoa25/retail-sales-data-agent † - retail data agent on Genie spaces
- https://github.com/databricks-solutions/caspers - fully simulated business demo (streaming data, agents)
- https://github.com/kawaiiblitz/cpg-audience-intelligence † - CPG audience intelligence on Databricks Apps

## Telecom, energy and utilities, supply chain
- https://github.com/databricks-industry-solutions/fraud_prevention_in_telco †
- https://github.com/databricks-industry-solutions/comtrade-accelerator - fault detection for electric utilities
- https://github.com/sourabhghose/genie_for_energy † - Genie Code workshop, energy edition
- https://github.com/databricks-industry-solutions/supply-chain-optimization
- https://github.com/databricks-industry-solutions/supply-chain-stress-test
- https://github.com/databricks-industry-solutions/routing - route generation
- https://github.com/rabailshafeeq/supply-chain-genie-agent † - natural-language BI on Genie for supply chain
- https://github.com/wscalioni/genie-code-vibe-lab - Genie Code lab on a synthetic logistics dataset

## Education
No public Genie/metric-view education repo was found on 2026-11-20. Use `industries/education.yaml` as a starting point and see the generic semantics repos above.

## Browse more
- Solution accelerators org: https://github.com/databricks-industry-solutions (search by industry keywords)
- Field solutions org: https://github.com/databricks-solutions
- Topic tag: https://github.com/topics/databricks-industry-solutions
