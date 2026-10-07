"""Make every product's display picture and thumbnail again.

    python manage.py rebuild_product_images [--missing-only]

From the stored original; an original that still carries EXIF or other
metadata (uploaded before originals were cleaned) is cleaned on the way.
--missing-only touches only products without a display picture, which is
every product after the display picture was introduced. One failing
picture is reported and the rest go on (after event-guestbook's
rebuild_thumbnails).
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from products.image_services import rebuild_product_image
from products.models import ProductProfile


class Command(BaseCommand):
    help = "Regenerate product display pictures and thumbnails from the originals."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--missing-only",
            action="store_true",
            help="Only products that have no display picture yet.",
        )

    def handle(self, *args, **options) -> None:
        profiles = (
            ProductProfile.objects.exclude(image="")
            .select_related("product")
            .order_by("pk")
        )

        if options["missing_only"]:
            profiles = profiles.filter(display="")

        rebuilt = 0
        failed = 0

        for profile in profiles.iterator():
            try:
                with transaction.atomic():
                    change = rebuild_product_image(profile=profile)
            except Exception as error:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f"{profile.product.sku}: {error}")
                )
            else:
                change.commit()
                rebuilt += 1
                self.stdout.write(f"Rebuilt {profile.product.sku}")

        summary = f"Rebuilt: {rebuilt}, failed: {failed}"

        if failed:
            self.stderr.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
