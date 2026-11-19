# ADR-005: Python Engineering Standards and Configuration Governance

- **Status:** Approved
- **Date:** 2026-11-19
- **Decision Makers:** @BereDarius
- **Related ADRs:** ADR-001, ADR-002, ADR-003, ADR-004

## 1. Context

The Japan Tourism Lakehouse project requires a consistent, maintainable and strongly governed Python codebase.

The ingestion framework is intended to be metadata-driven, extensible and independently testable. Its components must have clearly defined responsibilities and interfaces, while its configuration must be validated before execution.

Without established engineering standards, the project risks developing inconsistent coding practices, weak type guarantees, tightly coupled components and configuration errors that are only discovered at runtime.

The project therefore requires an opinionated engineering standard covering:

- Data contract specification and governance.
- Configuration structure and validation.
- Python type safety.
- Application architecture and module boundaries.
- Code quality and formatting.
- Testing and architectural enforcement.
- Continuous integration.

The objective is to establish these standards before implementing the ingestion framework.

## 2. Decision

The project adopts the following engineering standards.

| Concern                                  | Selected Standard                           |
| ---------------------------------------- | ------------------------------------------- |
| Data contract specification              | Open Data Contract Standard (ODCS) 3.2.0    |
| Engine-specific configuration validation | Pydantic v2                                 |
| Python architecture                      | Hexagonal Architecture (Ports and Adapters) |
| Static type checking                     | Pyright strict mode                         |
| Component interfaces                     | Python `Protocol`                           |
| Domain models                            | Standard Python dataclasses                 |
| Linting                                  | Ruff                                        |
| Formatting                               | Ruff formatter                              |
| Testing                                  | pytest                                      |
| Architecture enforcement                 | Import Linter                               |
| Dependency wiring                        | Explicit composition root                   |
| CI/CD enforcement                        | GitHub Actions                              |

The project will use Python 3.12 as its current supported runtime baseline, consistent with the existing project configuration.

## 3. Data Contract Governance

### 3.1 Open Data Contract Standard

ODCS version 3.2.0 is adopted as the standard for dataset contracts.

Data contracts describe the structure, semantics and expectations of datasets independently of the implementation of the ingestion engine.

ODCS contracts will be maintained as YAML files under:

```text
contracts/
└── datasets/
    └── accommodation_foreign_guest_nights.yaml
```

Contracts should capture relevant information such as:

- Dataset identity and description.
- Data ownership and source references.
- Schema and field definitions.
- Data types and constraints.
- Dataset grain and business semantics.
- Data quality expectations.
- Relevant dimensions, measures and relationships.
- Documentation and metadata references.

Contracts created by this project are consumer-side contracts. They describe the project's understanding and expectations of external datasets and must not imply that the original publisher guarantees properties that it has not documented.

Source-documented facts must be distinguishable from project-defined assumptions and validation expectations.

### 3.2 Contract Validation

ODCS documents must be validated against the official JSON Schema corresponding to ODCS version 3.2.0.

The schema version must be explicitly pinned. Schema validation is a structural validation mechanism and does not replace the full ODCS specification or any additional semantic checks required by the project.

Contract validation must be automated and executed as part of the development and CI workflows.

### 3.3 Separation of Data Contracts and Ingestion Configuration

Data contracts and ingestion configuration serve different purposes and must remain separate.

**Data contracts describe:**

- What the dataset represents.
- Its schema and semantics.
- Its expected grain.
- Its quality expectations.
- Its ownership and provenance.

**Ingestion manifests describe:**

- How the source is acquired.
- Which reader implementation is used.
- Reader-specific extraction options.
- The ingestion pattern.
- Artifact preservation requirements.
- The target storage destination.
- The associated data contract.

Ingestion manifests will be maintained under:

```text
conf/
└── ingestion/
    └── accommodation_foreign_guest_nights.yaml
```

Each ingestion manifest must reference its corresponding dataset contract.

### 3.4 Configuration Validation

Engine-specific ingestion manifests will be represented by Pydantic v2 models.

The following validation principles apply:

- Strict validation must be enabled.
- Unknown fields must be rejected.
- Required fields must be explicitly defined.
- Defaults must be intentional and documented.
- Invalid values must produce actionable validation errors.
- Environment-specific secrets must never be stored in configuration files.
- Cross-references between manifests and contracts must be validated.

Unvalidated dictionaries must not be passed through application services when a typed configuration model is available.

### 3.5 Data Quality Governance

Data quality expectations should primarily be declared in the ODCS contract.

The ingestion framework is responsible for implementing and executing the supported validation rules.

The framework may provide reusable validation implementations identified by stable rule identifiers. Rule-specific parameters may be supplied where necessary.

The same quality expectations must not be independently maintained in multiple configuration files without a clear reason.

## 4. Python Architecture

### 4.1 Hexagonal Architecture

The project adopts Hexagonal Architecture, also known as Ports and Adapters.

The architecture separates business concepts and application behavior from infrastructure implementations.

The principal architectural areas are:

**Domain**

Contains business concepts and rules.

Examples:

- Dataset identity.
- Ingestion run.
- Batch identity.
- Execution status.
- Domain exceptions.
- Domain value objects.

The domain must not depend on application or infrastructure implementations.

**Application**

Contains application use cases and orchestration logic.

Examples:

- Ingestion engine.
- Dataset ingestion workflow.
- Application services.
- Application ports and interfaces.

The application layer may depend on the domain and its own abstractions but must not depend on concrete infrastructure implementations.

**Infrastructure**

Contains implementations of the interfaces required by the application.

Examples:

- XLSX readers.
- HTTP source acquisition.
- Delta Lake writers.
- YAML metadata repositories.
- Execution tracking implementations.
- Artifact storage implementations.

Infrastructure implementations may depend on application interfaces and domain types.

### 4.2 Dependency Direction

Dependencies must point toward the inner architectural layers.

The following rules are mandatory:

1. Domain must not import application or infrastructure modules.
2. Application must not import concrete infrastructure implementations.
3. Infrastructure may implement interfaces defined by the application or domain.
4. Infrastructure implementations must not be imported directly by inner layers.
5. Concrete dependencies must be assembled in the composition root.
6. Circular dependencies between architectural layers or modules are prohibited.

Ports must be defined by the layer that requires the capability.

For example, `SourceReader` is an application port because the ingestion use case requires a source-reading capability.

### 4.3 Component Interfaces

Python `Protocol` will be the preferred mechanism for defining structural interfaces between components.

Interfaces must describe the behavior required by consuming components rather than the implementation details of individual adapters.

Implementations must be compatible with their corresponding protocols under static type checking.

Concrete implementation selection must be handled through an explicit registry or composition mechanism.

Runtime registration and validation must not be confused with static protocol compatibility.

### 4.4 Domain Models

Standard Python dataclasses will be the default mechanism for internal domain models.

Use frozen dataclasses for immutable value objects and other objects whose state must not change after construction.

Pydantic models should primarily be used for external configuration and data validation boundaries rather than as the default representation of all internal domain objects.

Domain models must not depend unnecessarily on infrastructure or external serialization libraries.

### 4.5 Dependency Injection

The project will use explicit dependency injection through a composition root.

Concrete infrastructure implementations will be constructed and provided to application services at the application boundary.

A third-party dependency injection container will not be introduced initially.

Composition should remain explicit and testable.

## 5. Python Type Safety

### 5.1 Pyright Strict Mode

Pyright strict mode is adopted as the mandatory static type-checking baseline.

The project must configure Pyright explicitly and execute it locally and in CI.

The following practices are required:

- Public functions and methods must have explicit parameter and return annotations.
- Class attributes must have explicit types where appropriate.
- Avoid `Any` and isolate unavoidable untyped external boundaries.
- Prefer explicit domain types over generic strings, dictionaries and untyped objects.
- Avoid unnecessary type suppression comments.
- Any type-checking exception must include a clear justification.
- Type-checking failures must block pull-request approval.

Static typing does not replace runtime validation of external data.

### 5.2 Runtime Validation

Pydantic v2 will provide runtime validation for engine-specific configuration and other explicitly defined external input boundaries.

Validation must occur before untrusted configuration enters the application workflow.

The project must not assume that Python type annotations alone guarantee runtime correctness.

## 6. Code Quality and Style

### 6.1 Ruff

Ruff is adopted for linting and formatting.

Its configuration will be maintained centrally in `pyproject.toml`.

The project will use an explicit, curated lint-rule selection rather than enabling every available rule without consideration.

Ruff formatting and linting must be consistent between local development and CI.

### 6.2 Mandatory Coding Practices

The following practices are required:

1. Follow PEP 8 naming and style conventions.
2. Provide explicit type annotations for public APIs.
3. Prefer small, cohesive modules and classes.
4. Prefer composition over inheritance.
5. Avoid global mutable state.
6. Avoid circular imports.
7. Avoid business logic inside infrastructure adapters.
8. Avoid generic utility modules that accumulate unrelated responsibilities.
9. Avoid broad exception handling that silently suppresses failures.
10. Use Python's standard logging facilities instead of `print()` for application logging.
11. Do not use assertions as a replacement for production input validation.
12. Keep constructors focused on establishing valid object state.
13. Document public APIs and non-obvious behavior with appropriate docstrings.
14. Do not introduce abstractions without a clear architectural or functional purpose.

### 6.3 Error Handling

Errors must be handled explicitly and consistently.

Domain-specific exceptions should represent meaningful application and business failures.

Infrastructure errors should be translated or propagated at appropriate boundaries without losing useful diagnostic context.

The ingestion engine must return structured execution results according to the lifecycle and failure-handling rules defined in ADR-004.

## 7. Testing Standards

pytest is adopted as the project's testing framework.

The following test categories will be maintained:

- Unit tests for isolated business logic and components.
- Integration tests for interactions between application and infrastructure implementations.
- Configuration tests for valid and invalid contracts and manifests.
- Architectural tests for dependency-boundary enforcement.

Tests must be deterministic and independent of external services unless explicitly classified as integration tests.

External infrastructure should be replaced by controlled test doubles when testing isolated application behavior.

Configuration validation must include both valid and invalid examples.

## 8. Architecture Enforcement

Import Linter will be used to enforce architectural dependency rules.

The project will define contracts that prohibit:

- Domain-to-application dependencies.
- Domain-to-infrastructure dependencies.
- Application-to-concrete-infrastructure dependencies.
- Circular dependencies between protected modules.

Architecture checks must run automatically in CI.

Exceptions to architectural rules require explicit justification and review.

## 9. Continuous Integration

GitHub Actions will enforce the project's engineering standards on pull requests.

The required checks will include:

1. Ruff linting.
2. Ruff formatting verification.
3. Pyright strict type checking.
4. ODCS contract validation.
5. Pydantic ingestion-manifest validation.
6. Import Linter architectural checks.
7. pytest unit tests.
8. Relevant integration tests.

All required checks must pass before a pull request is eligible for merge.

The same checks should be executable locally through documented commands.

## 10. Adoption Policy

The proposed adoption policy is progressive.

All new production code must comply with the standards defined in this ADR.

Existing code may be migrated incrementally rather than requiring a large, unrelated refactoring effort.

Changes to existing modules must not introduce additional violations of the established standards.

Exceptions must be explicitly justified and documented.

The project should gradually increase enforcement as the codebase becomes compliant.

## 11. Consequences

### Positive Consequences

- Consistent and predictable development practices.
- Stronger static and runtime type safety.
- Explicit architectural boundaries.
- Reduced coupling between business logic and infrastructure.
- Standardized and reusable data contracts.
- Early detection of configuration and implementation errors.
- Improved unit-testability and maintainability.
- Automated enforcement of engineering standards.
- Better onboarding for future contributors.
- A more credible and maintainable production-oriented portfolio project.

### Negative Consequences

- Additional development dependencies and configuration.
- More initial setup and CI complexity.
- Additional effort required to define and maintain data contracts.
- Strict type checking may require more explicit code.
- Architectural boundaries introduce some initial structural overhead.
- Some simple implementations may require additional interfaces or models.

These costs are accepted because the project prioritizes maintainability, correctness and architectural clarity.

## 12. Non-Goals

This ADR does not establish:

- A generic dependency injection framework.
- A universal plugin framework.
- A mandatory web application framework.
- A generic event-driven architecture.
- A requirement to use inheritance for all components.
- A requirement to introduce abstractions without an actual use case.
- A complete orchestration platform.
- A requirement to convert every external source into an ODCS contract published by its original owner.

These concerns may be addressed through future decisions if project requirements justify them.

## 13. References

- Open Data Contract Standard: https://bitol-io.github.io/open-data-contract-standard/
- Python Typing Specification: https://typing.python.org/
- Pyright: https://github.com/microsoft/pyright
- Pydantic: https://docs.pydantic.dev/
- Ruff: https://docs.astral.sh/ruff/
- pytest: https://docs.pytest.org/
- Import Linter: https://import-linter.readthedocs.io/
- Hexagonal Architecture: https://alistair.cockburn.us/hexagonal-architecture/

## 14. Change History

| Date       | Description                                                                    |
| ---------- | ------------------------------------------------------------------------------ |
| 2026-11-19 | Initial proposal of Python engineering standards and configuration governance. |
