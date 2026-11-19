# Japan Tourism Agency (JTA)

## Source identity

- **Organization:** Japan Tourism Agency (観光庁, JTA)
- **Parent ministry:** Ministry of Land, Infrastructure, Transport and Tourism (MLIT), Japan
- **Source type:** Government statistical publisher
- **Official accommodation statistics page:** https://www.mlit.go.jp/kankocho/tokei_hakusyo/shukuhakutokei.html
- **Official English copyright / terms page:** https://www.mlit.go.jp/kankocho/en/sitepolicy.html
- **Checked on:** 2026-11-19

## Overview

The Japan Tourism Agency publishes official tourism statistics. The Accommodation Survey (宿泊旅行統計調査) provides statistics about accommodation in Japan, including guest-nights and room occupancy. The official statistics page provides current results and historical data, including Excel workbooks.

This project currently uses the Accommodation Survey trend workbook as its first ingestion target. Other JTA datasets may be added after separate discovery and evaluation.

## Licensing and reuse

The JTA's English copyright policy states that, unless otherwise specified, the Public Data License (Version 1.0) applies to content published on its website. The Japanese-language policy is the original and prevails if there is a discrepancy with the English reference translation.

Before reusing an individual dataset or file:

1. Check the relevant dataset page and workbook for any dataset-specific terms or third-party material.
2. Follow the JTA's source-citation requirements and the applicable PDL 1.0 conditions.
3. If content is edited or transformed, clearly indicate that it has been modified and identify this project as the party responsible for the modifications.
4. Do not imply that derived data or analysis was created or endorsed by the Japanese government.
5. Re-check the terms when the source is updated; this profile is not a legal opinion.

Useful official references:

- JTA copyright policy: https://www.mlit.go.jp/kankocho/en/sitepolicy.html
- Public Data License (Version 1.0), English reference: https://www.digital.go.jp/en/resources/open_data/public_data_license_v1.0
- Digital Agency open-data page: https://www.digital.go.jp/en/resources/open_data

## Publication and revision considerations

The Accommodation Survey publishes monthly results and trend tables. The official page distinguishes publication stages such as first preliminary, second preliminary and definitive results. Values may be revised between publication stages, and the agency may publish correction notices or replace files.

For ingestion and downstream analysis:

- Preserve the publication stage and reference period as source metadata.
- Preserve each acquired original workbook as an immutable source artifact.
- Record retrieval time, source URL, file name and a cryptographic checksum.
- Treat a replacement or corrected workbook as a new acquired artifact/version; do not silently overwrite the previous raw artifact.
- Do not assume the URL or file address remains stable across republishing.

## Known methodology consideration

The Accommodation Survey changed its stratification basis from employee count to number of rooms beginning with 2026 data. The 2026 room-count strata are 1–9, 10–19, 20–39, 40–99, 100–199 and 200+ rooms.

This is a methodological discontinuity that must be represented in dataset metadata and considered when comparing periods. It does not automatically mean every comparison across the boundary is invalid; analysis should account for the change and consult the agency's explanatory material.

## Project usage

Current project dataset:

- Dataset ID: `accommodation_foreign_guest_nights`
- Dataset profile: [Accommodation Survey — foreign guest-nights trend](../datasets/accommodation-foreign-guest-nights.md)

## Source verification log

| Date checked | Item                               | Result                                                                  |
| ------------ | ---------------------------------- | ----------------------------------------------------------------------- |
| 2026-11-19   | Official Accommodation Survey page | Current results and historical workbooks are published there            |
| 2026-11-19   | JTA copyright policy               | English policy states PDL 1.0 applies unless otherwise specified        |
| 2026-11-19   | Methodology change                 | 2026 change to room-count-based stratification recorded for project use |

Revisit this profile when the source portal or terms change, and at least when onboarding a new JTA dataset.
