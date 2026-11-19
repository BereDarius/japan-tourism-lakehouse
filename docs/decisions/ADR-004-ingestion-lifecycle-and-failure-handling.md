# ADR-004: Ingestion Lifecycle, Component Responsibilities, and Failure Handling

- Status: Accepted
- Date: 2026-11-19
- Decision makers: @BereDarius

## Context

A metadata-driven ingestion framework needs a predictable execution
lifecycle so that datasets are processed consistently, failures are
observable, and individual components can be developed and tested
independently.

The framework must separate control-plane responsibilities (deciding
what should happen and tracking execution) from data-plane
responsibilities (acquiring, extracting, validating, and writing data).

The engine executes one dataset per invocation, as established by
ADR-003. It must support safe retries and recoverable execution when a
failure occurs between writing Bronze data and recording the final
execution status.

## Decision

The ingestion engine will coordinate this lifecycle for one dataset:

1.  Resolve the dataset metadata.
2.  Validate the metadata and configuration.
3.  Register an ingestion run.
4.  Acquire and preserve the source artifact where applicable.
5.  Resolve and invoke the configured source reader.
6.  Validate the extracted data.
7.  Write source-shaped data to Bronze.
8.  Finalize execution tracking and return a structured result.

Configuration resolution and validation occur before a normal ingestion
run is registered. If configuration cannot be resolved or validated, the
engine must still report the failure through its returned error/result
and application logging; it must not attempt source extraction or a
Bronze write.

Once a run is registered, failures in artifact acquisition, extraction,
data validation, or Bronze writing must be recorded against that run
whenever the tracking service is available. A successful Bronze write
followed by a failed final tracking update is an
uncertain/reconciliation state, not a clean failure that can be blindly
retried as a new append.

The framework separates control-plane and data-plane responsibilities.

### Control plane

- **Metadata Repository:** Loads dataset definitions from the
  configured metadata source.
- **Configuration Validator:** Validates required fields, supported
  settings, and internal consistency of dataset metadata.
- **Reader Registry:** Resolves a source reader for the configured
  source type or format.
- **Execution Tracker:** Registers runs and records status,
  timestamps, counts, artifact references, and error details.
- **Ingestion Engine:** Coordinates the lifecycle and delegates work
  to the responsible components.

### Data plane

- **Artifact Manager:** Acquires source artifacts, calculates content
  hashes, and preserves original artifacts where applicable.
- **Source Readers:** Extract source data from the configured source.
  Source-specific parsing belongs in the reader, not in the engine.
- **Data Quality Validator:** Executes configured technical and
  source-specific validation checks on extracted data.
- **Bronze Writer:** Writes source-shaped extracted data to the
  configured Bronze destination while adding ingestion lineage.

The engine must not contain source-format parsing logic, and source
readers must not own run tracking or Bronze persistence.

## Execution Tracking

The initial execution tracker will capture, where available:

- Run identifier and dataset identifier.
- Execution status.
- Start and completion timestamps.
- Source artifact identifier, location, and content hash.
- Reader or extraction configuration version where relevant.
- Number of records read and written.
- Error category and diagnostic message.

The initial run statuses are:

- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `RECONCILIATION_REQUIRED`

A run identifier represents an execution attempt. A retry may create a
new run identifier while retaining a deterministic identity for the
source artifact and intended ingestion batch.

## Idempotency and Recovery

The framework must avoid unintended duplicate Bronze appends when an
execution is retried.

A deterministic ingestion identity should be derived from stable inputs
such as the dataset identifier, source artifact content hash, source
object (for example, worksheet), and relevant extraction/version
information. The exact key and write protocol will be finalized during
implementation.

A pre-write check alone is not sufficient to guarantee exactly-once
behavior because a Delta write and an execution-tracking update are not
one atomic transaction. The implementation must support reconciliation
of uncertain outcomes, for example by recording a deterministic batch
identifier with the Bronze write and checking whether that batch has
already been committed before retrying.

The framework will not claim exactly-once execution until the write and
recovery protocol has been implemented and tested.

## Alternatives Considered

1.  **One monolithic ingestion function.** Rejected because source
    parsing, validation, storage, and tracking would be tightly coupled
    and difficult to test independently.
2.  **Source readers that also write to Bronze and update run status.**
    Rejected because readers would own responsibilities beyond
    extraction and would be difficult to reuse.
3.  **Separate components coordinated by a single-dataset engine.**
    Selected because it provides clear responsibilities and supports
    independent testing and extension.
4.  **Assume a retry is safe after any failure.** Rejected because a
    write may have succeeded even if the final status update failed,
    potentially causing duplicate appends.

## Consequences

### Positive

- **Predictable execution:** Every dataset follows the same high-level
  lifecycle.
- **Separation of concerns:** Metadata handling, source extraction,
  validation, storage, and tracking are independently owned.
- **Testability:** Components can be unit-tested independently, with
  integration tests for their interactions.
- **Operational visibility:** Run status, counts, artifacts, and
  errors can be inspected.
- **Safer recovery:** Deterministic batch identity and reconciliation
  reduce the risk of duplicate writes after interrupted executions.

### Negative

- **More components to maintain:** Clear separation introduces
  interfaces and coordination overhead.
- **Tracking complexity:** Failures can occur while recording
  failures, so operational logging and reconciliation are also
  required.
- **Idempotency complexity:** Reliable retries require a defined batch
  identity and write protocol rather than a simple status check.

## Implementation Considerations

- Define small interfaces for metadata access, source readers,
  artifact management, validation, Bronze writing, and execution
  tracking.
- Keep the engine as lifecycle coordinator; avoid embedding
  implementation details of individual components.
- Use structured execution results rather than relying only on printed
  log messages.
- Preserve original source artifacts and source-shaped Bronze data in
  accordance with ADR-001 and ADR-002.
- Add unit tests for configuration failures, reader resolution,
  validation failures, write failures, and result construction.
- Add integration tests for successful ingestion and recovery from an
  uncertain write outcome.
- Implement only the components and behavior required by the first
  real dataset; avoid introducing orchestration features into the
  engine.
