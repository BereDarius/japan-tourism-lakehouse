# ADR-002: Preserve Source Structure in Bronze

-   Status: Accepted
-   Date: 2026-11-19
-   Decision makers: @BereDarius

## Context

The lakehouse ingests external sources with different formats and
structures. Source schemas, publication versions, and transformation
requirements may change. If ingestion normalizes, reshapes, or applies
business transformations before storing data in Bronze, later changes
may require retrieving source data again.

The project needs a Bronze representation that retains source data as
close as practical to the delivered source while remaining queryable in
Delta Lake. For example, the Japan Tourism Agency accommodation trend
workbook has prefectures as rows and months as columns. Converting this
layout into one row per prefecture and month is useful standardization,
but it is a transformation rather than source capture.

## Decision

Bronze will preserve extracted source data in its original tabular shape
wherever practical. Ingestion will not perform business-level
normalization, aggregation, deduplication, or reshaping before writing
to Bronze.

For spreadsheets, this means preserving the worksheet's extracted row
and column structure, including its source column layout, while adding
clearly separated ingestion-lineage metadata. Bronze does not attempt to
preserve presentation features such as formatting, merged-cell
appearance, or visual layout.

Where practical, the original source artifact (for example, the
downloaded XLSX workbook) will also be retained unchanged in artifact
storage. The artifact provides a recoverable copy of the delivered
source; Bronze provides a queryable Delta representation of the
extracted source data.

Silver will perform standardization and structural transformations, such
as converting a wide monthly worksheet into a normalized long-form
dataset. Gold will contain business-facing models and aggregates.

Bronze records must retain sufficient lineage to identify the source
artifact, worksheet or source object, ingestion run, and extraction
time. Reprocessing downstream layers must use retained Bronze data and
versioned transformation logic rather than requiring another source
download.

## Alternatives Considered

1.  **Normalize data during ingestion.** Rejected because it couples
    source capture to transformation rules and can make later
    reprocessing dependent on retrieving the source again.
2.  **Store only the original binary source artifact.** Rejected as the
    sole representation because it is not directly queryable as a Delta
    table and requires repeated extraction for downstream processing.
3.  **Preserve source-shaped extracted data in Bronze and retain the
    original artifact where practical.** Selected because it balances
    queryability, source fidelity, lineage, and downstream flexibility.

## Consequences

### Positive

-   **Reprocessing flexibility:** Silver and Gold transformations can
    change without retrieving historical source files again.
-   **Source fidelity:** Bronze retains the source's extracted tabular
    structure rather than imposing analytical conventions.
-   **Separation of concerns:** Ingestion captures source data;
    downstream layers standardize and interpret it.
-   **Traceability:** Bronze records can be linked to the exact source
    artifact and worksheet.

### Negative

-   **More complex downstream processing:** Silver must handle
    source-specific layouts and convert them into consistent structures.
-   **Additional storage:** Retaining original artifacts and Bronze
    representations requires more storage.
-   **Source schema variability:** Changes in source worksheet layouts
    must be detected and handled explicitly.

## Implementation Considerations

### Original source artifacts

-   Preserve downloaded source files unchanged where practical.
-   Record a content hash (for example, SHA-256), source location,
    retrieval timestamp, and artifact storage location.
-   Do not commit downloaded source workbooks to the public Git
    repository unless there is a specific, reviewed reason.

### Bronze

-   Preserve extracted source rows and columns in their source-shaped
    layout.
-   Add lineage columns without silently changing source business
    values.
-   Identify the source artifact, worksheet, dataset, and ingestion run.
-   Retain deliveries append-only in accordance with ADR-001.

### Silver

-   Perform type standardization, header interpretation, reshaping,
    deduplication, and source-version reconciliation according to
    documented rules.
-   Preserve traceability to Bronze records and their source artifact.

### Gold

-   Build business-facing facts, dimensions, aggregates, and analytical
    models from Silver.
-   Do not modify retained Bronze source records.
