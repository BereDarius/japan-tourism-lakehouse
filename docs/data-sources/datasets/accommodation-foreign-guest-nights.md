# Accommodation Survey — Foreign Guest-Nights by Prefecture

## Dataset identity

| Property                                       | Value                                                             |
| ---------------------------------------------- | ----------------------------------------------------------------- |
| Dataset ID                                     | `accommodation_foreign_guest_nights`                              |
| Publisher                                      | Japan Tourism Agency (観光庁)                                     |
| Source survey                                  | Accommodation Survey (宿泊旅行統計調査)                           |
| Source profile                                 | [Japan Tourism Agency](../japan-tourism-agency/README.md)         |
| Official landing page                          | https://www.mlit.go.jp/kankocho/tokei_hakusyo/shukuhakutokei.html |
| Source workbook selected for initial profiling | `002028776.xlsx`                                                  |
| Worksheet                                      | `3-1`                                                             |
| Worksheet title                                | 都道府県別 外国人延べ宿泊者数 推移表（月別）                      |
| English description                            | Monthly trend of foreign guest-nights by prefecture               |
| Frequency                                      | Monthly                                                           |
| Geographic coverage                            | Japan total and 47 prefectures                                    |
| Initial profiled period                        | January–August 2026                                               |
| Initial publication status                     | Preliminary (confirm exact stage for each acquired release)       |
| Initial methodology version                    | `room_count_2026`                                                 |
| Ingestion pattern proposed                     | Full snapshot                                                     |
| Last profiled                                  | 2026-11-19                                                        |

> The workbook filename is a discovery-time identifier. The official publisher may replace download URLs or files. Always record the actual URL, retrieval timestamp, file checksum and source release details for each acquisition.

## Business purpose

This dataset measures overnight accommodation demand attributable to foreign guests across Japan and its prefectures. It can support analysis of geographic distribution, seasonality and changes in foreign guest-night activity.

It does **not** measure the number of unique foreign tourists or arrivals.

## Measure and grain

- **Measure:** foreign guest-nights (延べ宿泊者数, 外国人)
- **Unit:** person-nights (人泊)
- **Intended grain:** one observation per reference month and geography.
- **Geography:** one national total plus 47 prefectures.
- **Time grain:** calendar month.

A guest staying five nights contributes five guest-nights. Do not describe this measure as unique visitors, tourist arrivals or people unless a separate source measure supports that interpretation.

The survey's definition of foreign guests is based principally on guests without an address in Japan; nationality may be used as a proxy where address is difficult to determine. Confirm the exact definition against the explanatory notes accompanying each source release before publishing detailed interpretation.

## Source workbook structure

The selected workbook `002028776.xlsx` contains three trend worksheets:

| Worksheet | Subject               |
| --------- | --------------------- |
| `1-1`     | Total guest-nights    |
| `2-1`     | Japanese guest-nights |
| `3-1`     | Foreign guest-nights  |

The selected `3-1` worksheet was profiled with this layout:

| Worksheet rows | Content               |
| -------------- | --------------------- |
| 1              | Title                 |
| 2              | Unit                  |
| 3              | Reporting year        |
| 4              | Month headers         |
| 5              | Japan total           |
| 6–52           | 47 prefectures        |
| 53             | Preliminary-data note |

The layout is a profiling observation, not a permanent schema guarantee. The reader must validate the workbook and worksheet structure on every acquisition and fail clearly when the expected layout changes.

## Missing values and numeric observations

For the profiled 2026 worksheet:

- 48 geographic rows were present (Japan total plus 47 prefectures).
- January through August contained numeric observations.
- September through December were blank.
- The profile found 384 numeric observations and 192 blank month/geography cells.
- No explicit numeric zero was observed in those profiled cells.

**Important:** blank future months are missing/not-yet-published values, not zero. Preserve them as null. Do not fill blanks with zero during ingestion.

These counts describe the profiled workbook only. Recalculate them for every new release.

## Methodology and comparability

Beginning with 2026 data, the survey's stratification basis changed from number of employees to number of rooms. The room-count strata are:

- 1–9 rooms
- 10–19 rooms
- 20–39 rooms
- 40–99 rooms
- 100–199 rooms
- 200+ rooms

The previous methodology used employee-count-based strata. Represent the methodology explicitly, for example:

- `legacy_employee_count`
- `room_count_2026`

Do not silently treat the methodology as unchanged across the boundary. Comparisons may still be possible, but analysis must disclose and consider the methodology change and any agency guidance on comparability.

### Sampling design from 2026

Under the revised methodology:

- Accommodation facilities with 20 or more rooms are subject to a census survey.
- Facilities with 1–19 rooms are subject to sampling.
- Sampling rates for the sampled strata are determined by prefecture.

The JTA cautions that year-over-year comparisons may include the effects of this methodological change. Analytical outputs comparing 2025 and 2026 should disclose this limitation.

Official reference: [Changes associated with the revision of stratification criteria (JTA)](https://www.mlit.go.jp/kankocho/content/001983337.pdf).

## Publication status and revisions

The agency publishes results at different stages, including first preliminary, second preliminary and definitive values. Historical files may also be corrected.

For every acquired release, capture at least:

- reference period (the month/year measured)
- publication stage/status
- publication date, when available
- retrieval timestamp
- source URL
- source filename
- SHA-256 checksum
- methodology version
- ingestion batch/run identifiers

A corrected or later-stage workbook is a new source artifact/version. Preserve earlier artifacts and their ingestion history rather than overwriting them.

## Data quality expectations

The following checks are proposed for the selected worksheet:

1. Exactly one national total row is identified.
2. Exactly 47 prefecture rows are identified.
3. Prefecture identifiers are stored as strings where codes are used, preserving leading zeros.
4. Month columns are derived from source headers and reporting-year context, not hard-coded column positions alone.
5. Numeric observations are non-negative.
6. Blank source cells remain null.
7. The unit is captured as person-nights (`人泊`).
8. Source workbook, worksheet, publication status and methodology version are retained as provenance.
9. National total values are validated independently.
10. Do not require the sum of prefecture values to equal the national total exactly: the profiled workbook showed small differences. Investigate material deviations, but do not encode an unsupported exact-equality invariant.
11. Where total, Japanese and foreign worksheets are acquired for the same release, validate the relationship `total = Japanese + foreign` at matching geography/month grain, subject to source definitions, rounding and release alignment.

These are project-level validation expectations and should be revisited if the publisher changes the workbook structure or statistical methodology.

## Ingestion design notes

- **Pattern:** full snapshot for the selected trend workbook.
- **Bronze representation:** preserve the source-shaped worksheet data as agreed in ADR-002.
- **Source artifact:** retain the original XLSX file unchanged in artifact storage; record its checksum.
- **Worksheet selection:** `3-1` for this dataset.
- **Reprocessing:** Bronze should be rebuildable from the retained original artifact if extraction logic changes or a reader defect is found.
- **Silver:** normalize the wide month columns into a row-per-geography/per-month representation and apply validated geographic and temporal dimensions.
- **Gold:** define business facts and aggregates only after Silver semantics and quality rules are established.

Do not place the downloaded workbook in the public Git repository by default. Store it in the designated Bronze artifact location when the storage design is implemented.

## Attribution

Suggested attribution wording (verify against the applicable JTA terms and dataset-specific notices before publication):

> Source: Japan Tourism Agency, Accommodation Survey (宿泊旅行統計調査), [official statistics page](https://www.mlit.go.jp/kankocho/tokei_hakusyo/shukuhakutokei.html). Data processed and modified by the Japan Tourism Lakehouse project.

When publishing derived outputs, include the relevant source page, access/retrieval date and a clear indication that the data has been processed or modified. Do not imply government endorsement.

## Open questions / follow-up

- Confirm the exact publication stage and publication date associated with every downloaded workbook, rather than relying on a single static label.
- Capture the exact direct download URL at acquisition time.
- Confirm any dataset-specific terms or exceptions displayed alongside the current workbook.
- Validate the guest definition against the official explanatory notes for the exact release used.
- Define a stable prefecture dimension and code mapping, with an authoritative reference source.
- Re-profile the workbook whenever the publisher changes its layout.

## Change history

| Date       | Change                                                                                 |
| ---------- | -------------------------------------------------------------------------------------- |
| 2026-11-19 | Initial profile based on discovery and profiling of `002028776.xlsx`, worksheet `3-1`. |
| 2026-11-19 | Added the 2026 census/sampling design and official JTA methodology reference.          |
