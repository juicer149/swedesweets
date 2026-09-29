from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from retail.delivery_areas import (
    POSTAL_AREA_SNAPSHOT_PATH,
    PostalAreaFetchError,
    download_postal_areas,
    write_postal_area_snapshot,
)


class Command(BaseCommand):
    help = (
        "Download Haute-Savoie communes and postal codes from "
        "geo.api.gouv.fr and write the committed snapshot used by "
        "sync_retail_postal_areas. Run locally and commit the result; "
        "deploys never call the external API."
    )

    def handle(self, *args, **options) -> None:
        try:
            records = download_postal_areas()
        except PostalAreaFetchError as exc:
            raise CommandError(
                f"postal-area snapshot not updated: {exc}"
            ) from exc

        write_postal_area_snapshot(
            records,
        )

        postal_codes = {
            record.postal_code
            for record in records
        }

        self.stdout.write(
            f"Wrote {len(records)} postal areas "
            f"({len(postal_codes)} postal codes) to "
            f"{POSTAL_AREA_SNAPSHOT_PATH}"
        )
