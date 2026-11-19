# Japan Tourism Lakehouse 🇯🇵

An end-to-end Data Engineering project building a tourism analytics platform for Japan using **Databricks, PySpark, Python, SQL, and Delta Lake**.

The project aims to transform publicly available tourism statistics and geographic data into a reliable, analytics-ready data platform using modern Data Engineering principles and production-inspired software engineering practices.

## 🎯 Project Objectives

The primary objective is to design and implement a scalable lakehouse capable of supporting analytical questions about tourism in Japan.

Examples of questions the platform aims to answer:

- How does international tourism activity vary across Japanese prefectures?
- How does tourism activity change across different seasons?
- Which prefectures are experiencing the largest changes in visitor activity?
- How are tourist attractions distributed geographically across Japan?
- How do tourism trends differ between domestic and international visitors?
- How do accommodation trends correlate with geographic and seasonal factors?

The project will combine multiple public datasets to provide a broader understanding of tourism patterns.

## 🏗️ Architecture

The platform is designed around the **Medallion Architecture** pattern, separating data processing into Bronze, Silver, and Gold layers.

```text
                   DATA SOURCES
                         |
                         v
              +---------------------+
              |  INGESTION ENGINE   |
              | Metadata-driven     |
              | Single-dataset runs |
              +---------------------+
                         |
                         v
              +---------------------+
              |    BRONZE LAYER     |
              | Source-shaped data  |
              | Raw artifacts       |
              +---------------------+
                         |
                         v
              +---------------------+
              |    SILVER LAYER     |
              | Clean & Standardize |
              | Integrate & Validate|
              +---------------------+
                         |
                         v
              +---------------------+
              |     GOLD LAYER      |
              | Facts & Dimensions  |
              | Business Aggregates |
              +---------------------+
                         |
                         v
              +---------------------+
              |     ANALYTICS       |
              | SQL & Dashboards    |
              +---------------------+
```

### Metadata-driven ingestion framework

A central component of the project is a custom metadata-driven ingestion framework.

The framework is designed to:

- Execute ingestion for one dataset per invocation.
- Load and validate dataset metadata.
- Resolve the appropriate source reader.
- Acquire and preserve original source artifacts.
- Extract and validate source data.
- Write source-shaped data into Bronze.
- Track execution status and failures.
- Return structured execution results.

Dataset definitions will be maintained separately from ingestion implementation, allowing new datasets and source readers to be introduced without duplicating ingestion logic.

Orchestration and multi-dataset workflow management will remain separate from the ingestion engine.

### Bronze Layer

- Preserve source data in its original structural representation.
- Retain original file-based source artifacts.
- Capture ingestion metadata and source provenance.
- Support historical data tracking and reproducibility.
- Enable reprocessing independently of source availability.

### Silver Layer

- Clean and standardize incoming data.
- Integrate data from different sources.
- Handle missing values, duplicates and corrections.
- Apply data quality validations.
- Implement historical tracking where appropriate.
- Normalize source-specific structures into consistent analytical representations.

### Gold Layer

- Build dimensional models using facts and dimensions.
- Implement business-oriented aggregations.
- Combine tourism statistics with geographic reference data.
- Prepare analytics-ready datasets.

### Analytics

- Explore tourism patterns using Databricks SQL.
- Build dashboards and analytical views.
- Support business questions through reusable data models.

## 🛠️ Technology Stack

| Technology                         | Purpose                              |
| ---------------------------------- | ------------------------------------ |
| Python 3.12                        | Core programming language            |
| PySpark                            | Distributed data processing          |
| Databricks                         | Data Engineering platform            |
| Delta Lake                         | Reliable data storage                |
| SQL                                | Data transformations and analytics   |
| Open Data Contract Standard (ODCS) | Dataset contract specification       |
| Pydantic                           | Runtime configuration validation     |
| Pyright                            | Static type checking                 |
| Ruff                               | Code quality, linting and formatting |
| pytest                             | Automated testing                    |
| Import Linter                      | Architectural dependency enforcement |
| Git & GitHub                       | Version control and collaboration    |
| GitHub Actions                     | CI/CD automation                     |

Engineering tools and standards are introduced incrementally as the project evolves.

## 📊 Data Sources

The project is being built around publicly available tourism statistics and geographic datasets.

Potential and selected sources include:

| Source                                     | Data                                               |
| ------------------------------------------ | -------------------------------------------------- |
| Japan Tourism Agency (JTA)                 | Accommodation statistics and tourism surveys       |
| Japan National Tourism Organization (JNTO) | International visitor statistics                   |
| Japan Statistics Bureau                    | Official statistical and geographic reference data |
| OpenStreetMap                              | Geographic features and mapped tourist attractions |

Source discovery, dataset characteristics, licensing considerations, methodology and ingestion requirements are documented under [`docs/data-sources/`](docs/data-sources/).

**Data interpretation matters:** geographic feature counts from OpenStreetMap represent mapped features, not actual visitor numbers or attraction popularity. Tourism statistics and geographic datasets must be interpreted according to their respective definitions.

External datasets retain their own licensing and attribution requirements, independently of this repository's MIT license.

## 📋 Data Contract Governance

The project adopts the **Open Data Contract Standard (ODCS) 3.2.0** for documenting dataset contracts.

Data contracts describe:

- Dataset identity and business meaning.
- Schema and data types.
- Data grain and semantics.
- Data quality expectations.
- Ownership and source references.

Data contracts are separated from engine-specific ingestion manifests.

Ingestion manifests describe how datasets are acquired, extracted, validated and written into the lakehouse.

This separation keeps dataset contracts portable and ingestion implementation independent.

## 🧱 Software Architecture and Engineering Standards

The ingestion framework is designed around **Hexagonal Architecture (Ports and Adapters)**.

The architectural direction separates:

- **Domain:** Business concepts, entities, value objects and domain rules.
- **Application:** Use cases, ingestion workflows and component interfaces.
- **Infrastructure:** Concrete implementations such as source readers, storage writers and metadata repositories.

The project emphasizes:

- Strong static typing through Pyright strict mode.
- Runtime configuration validation through Pydantic.
- Explicit component interfaces using Python Protocols.
- Modular and reusable application components.
- Dependency inversion and separation of concerns.
- Automated architectural dependency checks.
- Reproducible and independently testable components.
- Documented architectural decisions (ADRs).

## 📁 Project Structure

The repository is organized around application responsibilities and engineering documentation.

```text
japan-tourism-lakehouse/
│
├── src/
│   └── japan_tourism/
│       ├── ingestion/
│       ├── transformations/
│       ├── quality/
│       └── common/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/
│   ├── architecture/
│   ├── decisions/
│   └── data-sources/
│
├── .github/
│   └── workflows/
│
├── databricks.yml
├── pyproject.toml
├── README.md
├── .gitignore
└── LICENSE
```

The structure will evolve as the framework and lakehouse layers are implemented.

## 🧪 Engineering Practices

The project aims to demonstrate professional Data Engineering and Software Engineering practices:

- Metadata-driven ingestion.
- Data contract governance.
- Medallion Architecture.
- Schema evolution and enforcement.
- Immutable raw data preservation.
- Data quality and validation.
- Historical data tracking and SCD strategies.
- Strong static typing and runtime validation.
- Modular and testable software architecture.
- Automated unit and integration testing.
- CI/CD and automated code quality checks.
- Git branching and Pull Request workflows.
- Architecture Decision Records (ADRs).
- Source documentation, data provenance and reproducibility.

## 🚀 Development Roadmap

- [x] Sprint 0 – Project setup and architecture foundation.
- [ ] Sprint 1 – Data source discovery and ingestion framework foundation.
- [ ] Sprint 2 – Bronze layer implementation.
- [ ] Sprint 3 – Silver layer transformations.
- [ ] Sprint 4 – Gold dimensional modelling.
- [ ] Sprint 5 – Data quality and automated testing.
- [ ] Sprint 6 – Analytics and dashboards.
- [ ] Sprint 7 – Documentation and deployment.

The roadmap may evolve as new technical requirements and datasets are discovered.

## 📈 Project Status

**Status:** Sprint 1 – Data Source Discovery and Ingestion Framework Foundation.

Current focus:

- Discovering and evaluating official Japanese tourism datasets.
- Documenting data sources and dataset characteristics.
- Defining the metadata-driven ingestion architecture.
- Establishing Python engineering and configuration standards.
- Preparing the foundation for the first ingestion pipeline.

Development is organized into incremental tasks and reviewed through GitHub Pull Requests.

## 📄 License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

External datasets, source files and third-party resources remain subject to their respective licenses and attribution requirements.

---

_Built as part of a long-term Data Engineering portfolio focused on modern data platforms, analytics, and AI engineering._
