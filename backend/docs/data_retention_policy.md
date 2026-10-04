# Data Retention Policy

This document outlines the data retention policies enforced within the Canteen Management Ecosystem (Phase 16).

## Retention Tiers

| Data Domain | Retention Period | Post-Retention Action | Justification |
| :--- | :--- | :--- | :--- |
| **Operational Telemetry** (e.g. active intelligence signals) | 90 days | Aggregated to Parquet/S3 | Real-time dashboards do not need raw data >90 days. |
| **Financial / Procurement** (e.g. Purchase Orders, Invoices) | 7 Years | Cold Storage / Immutable Ledger | Regulatory and institutional compliance. |
| **Customer PII** | Active account life + 30 days | Hard Deletion / Anonymization | GDPR / Institutional Privacy Policies. |
| **Outbox Events** | 30 days post-processing | Deletion | Replay window is typically <7 days. |
| **Audit Logs** | 1 Year | Cold Storage | Security and forensic traceability. |

## Implementation
In a production deployment, this policy is enforced via asynchronous CRON workers that query records where `created_at < (NOW() - retention_period)`. Data that requires cold storage is exported before deletion from the OLTP database.
