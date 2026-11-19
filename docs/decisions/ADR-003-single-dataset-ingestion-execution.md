# ADR-003: Single-Dataset Ingestion Execution Boundary

- Status: Accepted
- Date: 2026-11-19
- Decision makers: @BereDarius

## Context

The lakehouse needs a reusable ingestion framework that can process
multiple datasets over time. The framework should have a clear, testable
responsibility and should not become coupled to scheduling, workflow
management, or cross-dataset dependency handling.

Multiple datasets may eventually need to run sequentially or in
parallel. Those are orchestration concerns and can evolve independently
from the logic that ingests one dataset. The project may later evaluate
a separate orchestration application, Databricks Workflows, or a hybrid
approach. That decision has not yet been made.

## Decision

The ingestion engine will execute exactly one dataset per invocation.

The engine's public entry point will accept a dataset identifier,
resolve its metadata, execute the ingestion lifecycle for that dataset,
record the outcome, and return a structured result.

The engine will not be responsible for:

- Scheduling or triggering executions.
- Selecting or coordinating multiple datasets.
- Running multiple dataset ingestions in parallel.
- Managing dependencies or execution order between datasets.
- Providing cross-dataset workflow state or aggregated workflow
  results.

These responsibilities belong to a separate orchestration component or
platform. The orchestration technology and deployment model are deferred
to a future architecture decision.

The engine may use platform services such as Databricks, Spark, and
Delta Lake. Separating orchestration from the engine does not, by
itself, require separating compute or storage from Databricks.

## Alternatives Considered

1.  **Multi-dataset engine with built-in orchestration.** Rejected for
    the initial implementation because it combines dataset ingestion
    with scheduling, parallelism, dependency management, and workflow
    concerns.
2.  **Single-dataset engine with a separate orchestration boundary.**
    Selected because it keeps the engine focused, independently
    testable, and reusable by different orchestrators.
3.  **Implement an external orchestrator immediately.** Deferred because
    orchestration requirements are not yet sufficiently understood and
    are not needed to validate the single-dataset framework.

## Consequences

### Positive

- **Clear responsibility:** The engine ingests one configured dataset
  and reports the result.
- **Independent testing:** Dataset ingestion can be tested without a
  scheduler or multi-dataset execution environment.
- **Orchestration flexibility:** An external application, Databricks
  Workflows, or another orchestrator can invoke the same engine.
- **Simpler initial implementation:** Parallelism, scheduling, and
  dependency management do not complicate the first framework version.

### Negative

- **No built-in scheduling:** A separate mechanism is required to
  trigger ingestion.
- **No cross-dataset coordination:** Dependencies and aggregate
  workflow status must be implemented outside the engine if required.
- **Additional integration work later:** An orchestrator will need a
  stable invocation contract and a way to consume structured results.

## Implementation Considerations

- Provide a single-dataset API, conceptually
  `engine.ingest(dataset_id)`.
- Return a structured result containing at least the run identifier,
  dataset identifier, status, record counts where available, source
  artifact identity, and error details where applicable.
- Keep the engine independent of any specific orchestration product.
- Do not introduce `ingest_many`, scheduling, parallel execution, or
  dependency graph features into the initial engine.
- Revisit orchestration as a separate architecture decision after the
  single-dataset ingestion lifecycle is implemented and validated.
