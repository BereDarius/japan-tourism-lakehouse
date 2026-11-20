import argparse
import logging
from collections.abc import Sequence

from japan_tourism.bootstrap.ingestion import create_ingestion_engine
from japan_tourism.bootstrap.settings import IngestionSettings
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="japan-tourism-ingest",
        description="Ingest one Japan tourism dataset into Bronze.",
    )

    parser.add_argument(
        "dataset_id",
        help="Dataset identifier defined in conf/ingestion.",
    )
    parser.add_argument(
        "source_url",
        help="Direct HTTP(S) URL of the source artifact.",
    )
    parser.add_argument(
        "--publication-stage",
        default=None,
        help="Optional source publication stage, e.g. preliminary.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    args = create_parser().parse_args(argv)

    try:
        dataset_id = DatasetId(args.dataset_id)

        settings = IngestionSettings.from_environment()
        engine = create_ingestion_engine(settings)

        result = engine.execute(
            dataset_id=dataset_id,
            source_url=args.source_url,
            publication_stage=args.publication_stage,
        )

    except Exception:
        logger.exception("Ingestion execution failed.")
        return 1

    logger.info(
        "Ingestion finished: dataset_id=%s run_id=%s status=%s bronze_records_written=%s",
        result.dataset_id,
        result.run_id,
        result.status.value,
        result.bronze_records_written,
    )

    if result.status == IngestionStatus.SUCCEEDED:
        return 0

    if result.status == IngestionStatus.FAILED:
        logger.error("Ingestion failed: %s", result.error_message)
        return 1

    if result.status == IngestionStatus.RECONCILIATION_REQUIRED:
        logger.error("Reconciliation required: %s", result.error_message)
        return 2

    raise RuntimeError(f"Unexpected terminal status: {result.status}")
