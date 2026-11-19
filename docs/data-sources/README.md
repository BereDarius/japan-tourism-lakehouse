# Data sources

This directory documents the external sources used by the Japan Tourism Lakehouse.

The documentation is intentionally separate from ingestion configuration:

- **Source profiles** describe publishers, source portals, licensing, publication practices and source-level limitations.
- **Dataset profiles** describe a specific dataset's meaning, structure, grain, known quirks and ingestion requirements.
- **YAML metadata** (introduced with the ingestion framework) will contain the machine-readable settings required to execute ingestion. It should reference these documents rather than duplicate long-form explanations.

## Source register

| Source ID              | Publisher                  | Scope                                                           | Documentation                                          |
| ---------------------- | -------------------------- | --------------------------------------------------------------- | ------------------------------------------------------ |
| `japan_tourism_agency` | Japan Tourism Agency (JTA) | Official tourism statistics, including accommodation statistics | [Japan Tourism Agency](japan-tourism-agency/README.md) |

## Dataset register

| Dataset ID                           | Source               | Description                                      | Documentation                                                                |
| ------------------------------------ | -------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------- |
| `accommodation_foreign_guest_nights` | Japan Tourism Agency | Monthly foreign guest-nights by Japan/prefecture | [Foreign guest-nights trend](datasets/accommodation-foreign-guest-nights.md) |

## Documentation conventions

- Prefer official publisher pages and original source files.
- Record the date on which a source page or file was checked.
- Keep the original source URL even if a downloaded file is stored in Bronze.
- Treat publication status (preliminary, revised, definitive) as data provenance.
- Record methodology changes explicitly; do not silently combine series with different methodologies.
- Do not commit downloaded source workbooks to the public Git repository unless redistribution rights have been checked and there is a clear reason to include them.
- When data is transformed or republished, retain attribution and clearly state that the project has modified the source data.

## Maintenance

Update a source or dataset profile whenever its source URL, license terms, file structure, definitions, publication lifecycle, methodology or ingestion assumptions change.
