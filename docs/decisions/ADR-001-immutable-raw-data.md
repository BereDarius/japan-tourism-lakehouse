# ADR-001: Immutable Raw Data and Independent Transformation Layers

- Status: Accepted
- Date: 2026-11-17
- Decision makers: @BereDarius

## Context

Source data may arrive on different schedules, contain duplicates or
corrections, and change structure over time. Overwriting records during
ingestion can erase prior values, making historical analysis and lineage
difficult. Transformation rules and schemas also evolve, so derived data may
need to be rebuilt from earlier inputs. Reprocessing should not depend on
retrieving the same historical data from source systems again, which may be
impossible or costly. These challenges require preserving source history and
managing ingestion separately from downstream transformations.

## Decision

Raw data will be ingested append-only. Every delivery, including duplicates and corrections, will be retained as received during its retention period; existing raw records will not be overwritten or modified during that period. This decision establishes immutability, but does not define how long raw data must be retained. Ingestion metadata will record provenance, such as the source, arrival time, and batch identifier.

Ingestion will capture source records, while validation, deduplication, consolidation, and business transformations will take place downstream. This separation preserves original inputs and allows transformation logic to change independently.

Downstream layers will maintain consolidated representations of source data, applying documented rules to resolve duplicates and corrections. Where historical attribute changes must be tracked, the representation will use SCD Type 2: preserve prior versions with effective-time boundaries and identify the current version. SCD Type 2 is required only for data with this historical-tracking need.

Downstream data must be reproducible from retained raw records and versioned transformation logic. Reprocessing will rebuild or update derived data from those records without unnecessary retrieval from source systems.

If a raw-data lifecycle policy is introduced, archival to lower-cost storage is preferred to deletion. Deletion requires an explicitly approved retention or compliance requirement and an assessment of its impact on historical reprocessing; reproducibility is limited to the raw data that remains retained.

## Alternatives Considered

1. Directly overwrite existing source records. Rejected because overwriting can erase history and limit reproducibility.
2. Combine ingestion and transformation in one pipeline. Rejected because it couples source capture to changing validation and transformation logic.
3. Maintain append-only raw data and independent downstream processing. Selected because it preserves source history and allows derived data to be rebuilt as transformation logic evolves.

## Consequences

### Positive

- **Historical traceability:** Retaining every delivery, including duplicates and corrections, preserves the source history and its provenance.
- **Reproducibility:** Derived data can be rebuilt from retained raw records and versioned transformation logic without relying on source-system retrieval.
- **Better separation of concerns:** Ingestion captures source records, while downstream layers independently handle validation, deduplication, consolidation, and business transformations.
- **Easier recovery and reprocessing:** If downstream data or transformation logic changes, derived layers can be rebuilt or updated from retained raw records.

### Negative

- **Increased storage requirements:** Append-only retention keeps duplicates, corrections, and prior deliveries, requiring more storage than overwriting records. A future lifecycle policy should prefer archiving older records to lower-cost storage. Deletion should occur only for an explicitly approved retention or compliance requirement, after assessing the impact on historical reprocessing.
- **More complex change detection:** Downstream processing must identify duplicates and corrections and apply documented rules to consolidate them.
- **Additional processing and metadata management:** Provenance, batch details, and transformation versions must be maintained, and derived data must be rebuilt or updated when needed.

## Implementation Considerations

### Bronze

Bronze will retain every source delivery append-only, including duplicates and
corrections, without overwriting prior records. It will preserve source
records with provenance metadata such as source, arrival time, and batch
identifier, keeping capture separate from downstream transformations.

### Silver

Silver will validate, deduplicate, and consolidate Bronze records according to
documented rules for duplicates and corrections. Where historical attribute
changes must be tracked, Silver will use SCD Type 2 versions with effective-time
boundaries and a current-version indicator. Silver outputs will be
reproducible from retained Bronze data and versioned transformation logic.
When implementing SCD Type 2, distinguish source effective time (when an
attribute was true at the source) from system or ingestion time (when the
lakehouse received or recorded it), and define how both are represented.

### Gold

Gold will build business-facing models and aggregates from Silver. These
derived outputs can be rebuilt or updated when upstream data or transformation
logic changes; Gold processing will not alter the retained Bronze source
records.
