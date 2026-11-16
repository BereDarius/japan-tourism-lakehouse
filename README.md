# Japan Tourism Lakehouse 🇯🇵

An end-to-end Data Engineering project that builds a tourism analytics platform for Japan using **Databricks, PySpark, Python, SQL, and Delta Lake**.

The project aims to transform publicly available tourism and geographic data into a reliable, analytics-ready data platform using modern Data Engineering practices.

## 🎯 Project Objectives

The main objective is to design and implement a scalable data platform capable of answering business questions about tourism in Japan.

Examples of questions the platform should eventually answer:

- Which Japanese cities attract the most international tourists?
- How does tourism activity vary across different seasons?
- Which prefectures are becoming increasingly popular?
- What are the most popular tourist attractions?
- How do tourism trends differ between domestic and international visitors?

## 🏗️ Architecture

The platform will follow the **Medallion Architecture** pattern.

```text
              DATA SOURCES
                    |
                    v
          +-------------------+
          |   BRONZE LAYER    |
          |   Raw Data        |
          +-------------------+
                    |
                    v
          +-------------------+
          |   SILVER LAYER    |
          | Clean & Transform |
          +-------------------+
                    |
                    v
          +-------------------+
          |    GOLD LAYER     |
          | Analytics Models  |
          +-------------------+
                    |
                    v
          +-------------------+
          |     ANALYTICS     |
          | SQL & Dashboards  |
          +-------------------+
```

### Bronze Layer
- Ingest raw data from external sources.
- Preserve source data and ingestion metadata.
- Support historical data tracking.

### Silver Layer
- Clean and standardize incoming data.
- Handle missing values and duplicates.
- Apply data quality validations.
- Implement reusable transformation logic.

### Gold Layer
- Build dimensional models using facts and dimensions.
- Implement business-oriented aggregations.
- Prepare analytics-ready datasets.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| PySpark | Distributed data processing |
| Databricks | Data Engineering platform |
| Delta Lake | Reliable data storage |
| SQL | Data transformations and analytics |
| Git & GitHub | Version control |
| pytest | Automated testing |
| Ruff | Code quality and linting |
| GitHub Actions | CI/CD automation |

## 📊 Data Sources

The project will explore publicly available datasets, including:

- Japanese tourism statistics.
- Japan National Tourism Organization (JNTO) publications.
- Japan Statistics Bureau datasets.
- OpenStreetMap geographic and attraction data.
- Public geographic reference datasets.

Data source selection and ingestion strategies will be documented as the project evolves.

## 📁 Project Structure

The repository structure will evolve throughout development.

The intended structure is:

```text
japan-tourism-lakehouse/
│
├── src/
│   └── japan_tourism/
│
├── tests/
│
├── notebooks/
│
├── resources/
│
├── databricks/
│
├── docs/
│
├── .github/
│   └── workflows/
│
├── pyproject.toml
├── README.md
├── .gitignore
└── LICENSE
```

## 🧪 Engineering Practices

This project aims to demonstrate professional Data Engineering practices:

- Modular and reusable code.
- Incremental data ingestion.
- Schema evolution and enforcement.
- Data quality and validation.
- Automated unit and integration testing.
- CI/CD pipelines.
- Git branching and Pull Request workflows.
- Documentation of architectural decisions.

## 🚀 Development Roadmap

- [ ] Sprint 0 – Project setup and architecture.
- [ ] Sprint 1 – Data source discovery and ingestion.
- [ ] Sprint 2 – Bronze layer implementation.
- [ ] Sprint 3 – Silver layer transformations.
- [ ] Sprint 4 – Gold dimensional modelling.
- [ ] Sprint 5 – Data quality and automated testing.
- [ ] Sprint 6 – Analytics and dashboards.
- [ ] Sprint 7 – Documentation and deployment.

## 📈 Project Status

**Status:** Initial development / Sprint 0.

This project is being developed incrementally, with a focus on practical implementation and production-inspired engineering standards.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

*Built as part of a long-term Data Engineering portfolio focused on modern data platforms, analytics, and AI engineering.*
