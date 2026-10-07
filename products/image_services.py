from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from django.core.files.storage import Storage
from django.core.files.uploadedfile import UploadedFile

from products.image_processing import (
    ProcessedProductImage,
    has_metadata,
    process_product_image,
)
from products.models import (
    Product,
    ProductProfile,
)


@dataclass(frozen=True, slots=True)
class StoredImageFile:
    storage: Storage
    name: str


@dataclass(frozen=True, slots=True)
class ProductImageChange:
    """Files affected by one product image mutation.

    Database transactions do not include external file storage.

    rollback() removes newly written files.
    commit() removes files replaced by the successful mutation.
    """

    new_files: tuple[
        StoredImageFile,
        ...,
    ] = ()

    old_files: tuple[
        StoredImageFile,
        ...,
    ] = ()

    @classmethod
    def empty(
        cls,
    ) -> ProductImageChange:
        return cls()

    def rollback(self) -> None:
        _delete_stored_files(
            self.new_files
        )

    def commit(self) -> None:
        _delete_stored_files(
            self.old_files
        )


def change_product_image(
    *,
    product: Product,
    uploaded_image: UploadedFile | None = None,
    remove_image: bool = False,
) -> ProductImageChange:
    """Replace or remove the product catalog image.

    No upload and remove_image=False means no change.
    """

    if (
        uploaded_image is None
        and not remove_image
    ):
        return (
            ProductImageChange.empty()
        )

    if (
        uploaded_image is not None
        and remove_image
    ):
        raise ValueError(
            (
                "Cannot upload and remove "
                "a product image in the same operation."
            )
        )

    profile = (
        ProductProfile.objects
        .select_for_update()
        .get(
            product=product
        )
    )

    old_files = _profile_files(
        profile
    )

    if remove_image:
        profile.image = ""
        profile.display = ""
        profile.thumbnail = ""

        profile.save(
            update_fields=[
                "image",
                "display",
                "thumbnail",
            ]
        )

        return ProductImageChange(
            old_files=old_files,
        )

    assert uploaded_image is not None

    new_files: list[
        StoredImageFile
    ] = []

    try:
        processed = process_product_image(
            uploaded_image,
            original_name=uploaded_image.name,
        )

        _store_processed(
            profile=profile,
            processed=processed,
            new_files=new_files,
        )
    except Exception:
        _delete_stored_files(
            new_files
        )
        raise

    return ProductImageChange(
        new_files=tuple(
            new_files
        ),
        old_files=old_files,
    )


def rebuild_product_image(
    *,
    profile: ProductProfile,
) -> ProductImageChange:
    """Make the display picture and thumbnail again from the stored
    original, and clean the original too if it still carries metadata
    (stored before originals were cleaned). A clean original is left as
    it is, so a rebuild never re-encodes it.

    Call commit() after the transaction to delete the replaced files.
    """

    if not profile.image:
        return ProductImageChange.empty()

    with profile.image.open("rb") as original:
        processed = process_product_image(
            original,
            original_name=profile.image.name,
        )
        clean_original = has_metadata(original)

    replaced = [
        StoredImageFile(storage=field.storage, name=field.name)
        for field in (profile.display, profile.thumbnail)
        if field
    ]
    if clean_original:
        replaced.append(
            StoredImageFile(
                storage=profile.image.storage,
                name=profile.image.name,
            )
        )

    new_files: list[StoredImageFile] = []
    fields = [
        ("display", processed.display),
        ("thumbnail", processed.thumbnail),
    ]
    if clean_original:
        fields.insert(0, ("image", processed.original))

    try:
        for field_name, content in fields:
            field = getattr(profile, field_name)
            field.save(content.name, content, save=False)
            new_files.append(
                StoredImageFile(storage=field.storage, name=field.name)
            )

        profile.save(update_fields=[name for name, _ in fields])
    except Exception:
        _delete_stored_files(new_files)
        raise

    return ProductImageChange(
        new_files=tuple(new_files),
        old_files=tuple(replaced),
    )


def _store_processed(
    *,
    profile: ProductProfile,
    processed: ProcessedProductImage,
    new_files: list[StoredImageFile],
) -> None:
    """Write the original, display picture and thumbnail to storage and
    the profile; each written file is added to new_files as it lands, so
    a failure part way can remove them."""

    for field_name, content in (
        ("image", processed.original),
        ("display", processed.display),
        ("thumbnail", processed.thumbnail),
    ):
        field = getattr(profile, field_name)
        field.save(content.name, content, save=False)
        new_files.append(
            StoredImageFile(storage=field.storage, name=field.name)
        )

    profile.save(
        update_fields=[
            "image",
            "display",
            "thumbnail",
        ]
    )


def _profile_files(
    profile: ProductProfile,
) -> tuple[
    StoredImageFile,
    ...,
]:
    return tuple(
        StoredImageFile(storage=field.storage, name=field.name)
        for field in (profile.image, profile.display, profile.thumbnail)
        if field
    )



def _delete_stored_files(
    stored_files: Iterable[
        StoredImageFile
    ],
) -> None:
    for stored_file in reversed(
        tuple(stored_files)
    ):
        if not stored_file.name:
            continue

        stored_file.storage.delete(
            stored_file.name
        )
