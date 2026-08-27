#!/opt/venvs/securedrop-app-code/bin/python

"""
Loads fixed test data from a YAML file into the SecureDrop database.
"""

import argparse
import datetime
import io
import os
import shutil
from pathlib import Path
from typing import Any

import journalist_app
import yaml
from db import db
from encryption import EncryptionManager
from models import (
    Journalist,
    Reply,
    SeenFile,
    SeenMessage,
    SeenReply,
    Source,
    Submission,
)
from sdconfig import SecureDropConfig
from source_user import create_source_user
from store import Storage


def verify_empty_database() -> None:
    """Verify that the database is empty before importing data."""
    tables_to_check = [
        (Journalist, "journalists"),
        (Source, "sources"),
        (Submission, "submissions"),
        (Reply, "replies"),
        (SeenFile, "seen_files"),
        (SeenMessage, "seen_messages"),
        (SeenReply, "seen_replies"),
    ]

    non_empty_tables = []
    for model, table_name in tables_to_check:
        count = model.query.count()
        if count > 0:
            non_empty_tables.append(f"{table_name} ({count} records)")

    if non_empty_tables:
        raise RuntimeError(
            f"Database is not empty. Found records in: {', '.join(non_empty_tables)}. "
            "Please start with a clean database."
        )


def import_journalists(journalists_data: list[dict[str, Any]]) -> dict[str, Journalist]:
    uuid_to_journalist = {}

    print(f"Importing {len(journalists_data)} journalists...")

    for i, journalist_data in enumerate(journalists_data, 1):
        username = journalist_data["username"]
        uuid = journalist_data["uuid"]
        journalist = Journalist(
            username=username,
            password=journalist_data["passphrase"],
            first_name=journalist_data["first_name"],
            last_name=journalist_data["last_name"],
            is_admin=bool(journalist_data["is_admin"]),
        )
        journalist.uuid = uuid
        journalist.otp_secret = journalist_data["otp_secret"]
        journalist.is_totp = True
        journalist.created_on = datetime.datetime.fromisoformat(journalist_data["created_on"])

        db.session.add(journalist)
        uuid_to_journalist[uuid] = journalist

        print(f"Imported journalist {i}/{len(journalists_data)}: {username}")

    db.session.commit()
    return uuid_to_journalist


def import_sources(sources_data: list[dict[str, Any]], yaml_dir: Path) -> dict[str, Source]:
    """Import sources from YAML data, loading PGP keys from separate files."""
    uuid_to_source = {}

    print(f"Importing {len(sources_data)} sources...")

    for i, source_data in enumerate(sources_data, 1):
        uuid = source_data["uuid"]
        journalist_designation = source_data["journalist_designation"]
        fingerprint = source_data["pgp_fingerprint"]

        # Load PGP keys from paths relative to YAML file
        public_key_path = source_data["pgp_public_key"]
        secret_key_path = source_data["pgp_secret_key"]

        public_key_file = yaml_dir / public_key_path
        secret_key_file = yaml_dir / secret_key_path

        public_key = public_key_file.read_text().strip()
        secret_key = secret_key_file.read_text().strip()

        # Create a source with real filesystem_id (using create_source_user)
        # We'll use a dummy passphrase since we're overriding the PGP keys anyway
        dummy_passphrase = f"dummy passphrase for {journalist_designation}"
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=dummy_passphrase,
            source_app_storage=Storage.get_default(),
        )
        source = source_user.get_db_record()

        source.journalist_designation = journalist_designation
        source.pgp_public_key = public_key
        source.pgp_secret_key = secret_key
        source.pgp_fingerprint = fingerprint
        source.uuid = uuid
        source.last_updated = datetime.datetime.fromisoformat(source_data["last_updated"])
        source.pending = False

        db.session.add(source)
        uuid_to_source[uuid] = source

        print(f"Imported source {i}/{len(sources_data)}: {journalist_designation}")

    db.session.commit()
    return uuid_to_source


def record_source_interaction(source: Source) -> None:
    source.interaction_count += 1
    # unlike loaddata.py, we don't update last_updated here so it uses the YAML value
    db.session.flush()


def import_submissions_and_replies(
    sources_data: list[dict[str, Any]],
    uuid_to_source: dict[str, Source],
    uuid_to_journalist: dict[str, Journalist],
    yaml_dir: Path,
    save_items: bool = False,
) -> tuple[dict[str, Submission], dict[str, Reply]]:
    uuid_to_submission = {}
    uuid_to_reply = {}
    storage = Storage.get_default()
    encryption_mgr = EncryptionManager.get_default()

    # Create items directory if saving items
    items_dir = yaml_dir / "items"
    if save_items:
        items_dir.mkdir(exist_ok=True)

    total_items = sum(len(source_data["items"]) for source_data in sources_data)
    submission_count = 0
    reply_count = 0

    print(f"Importing {total_items} items (messages, files, and replies)...")

    for source_data in sources_data:
        source = uuid_to_source[source_data["uuid"]]

        for item_data in source_data["items"]:
            uuid = item_data["uuid"]
            kind = item_data["kind"]

            # Record interaction (updates interaction_count, etc.)
            record_source_interaction(source)

            if kind == "message":
                # Message submission
                submission_count += 1
                content = item_data["content"]
                fpath = storage.save_message_submission(
                    source.filesystem_id,
                    source.interaction_count,
                    source.journalist_filename,
                    content,
                )
                submission = Submission(source, fpath, storage)
                submission.uuid = uuid
                submission.downloaded = item_data["downloaded"]

                encrypted_file_path = storage.path(source.filesystem_id, fpath)

                # Save encrypted item if flag is set
                if save_items:
                    saved_item_path = items_dir / f"{uuid}.gpg"
                    shutil.copy2(encrypted_file_path, saved_item_path)

                # Override with pre-encrypted file if specified in YAML
                if "encrypted_file" in item_data:
                    pre_encrypted_path = yaml_dir / item_data["encrypted_file"]
                    shutil.copy2(pre_encrypted_path, encrypted_file_path)
                    print(f"Imported message submission (pre-encrypted): {fpath}")
                else:
                    print(
                        f"Warning: no pre-encrypted file for message submission: {fpath}, "
                        "may be unreproducible"
                    )
                    print(f"Imported message submission: {fpath}")

                db.session.add(submission)
                uuid_to_submission[uuid] = submission

            elif kind == "file":
                # File submission
                submission_count += 1
                file_content = item_data["file"]["content"]
                original_filename = item_data["file"]["filename"]

                file_bytes = file_content.encode("utf-8")
                fpath = storage.save_file_submission(
                    source.filesystem_id,
                    source.interaction_count,
                    source.journalist_filename,
                    original_filename,
                    io.BytesIO(file_bytes),
                )
                submission = Submission(source, fpath, storage)
                submission.uuid = uuid
                submission.downloaded = item_data["downloaded"]

                encrypted_file_path = storage.path(source.filesystem_id, fpath)

                # Save encrypted item if flag is set
                if save_items:
                    saved_item_path = items_dir / f"{uuid}.gpg"
                    shutil.copy2(encrypted_file_path, saved_item_path)

                # Override with pre-encrypted file if specified in YAML
                if "encrypted_file" in item_data:
                    pre_encrypted_path = yaml_dir / item_data["encrypted_file"]
                    shutil.copy2(pre_encrypted_path, encrypted_file_path)
                    print(f"Imported file submission (pre-encrypted): {fpath}")
                else:
                    print(
                        f"Warning: no pre-encrypted file for file submission: {fpath}, "
                        "may be unreproducible"
                    )
                    print(f"Imported file submission: {fpath}")

                db.session.add(submission)
                uuid_to_submission[uuid] = submission

            elif kind == "reply":
                # Reply
                reply_count += 1
                journalist_uuid = item_data["journalist_uuid"].split(" ")[0]  # Remove comment part
                journalist = uuid_to_journalist[journalist_uuid]
                content = item_data["content"]

                fname = f"{source.interaction_count}-{source.journalist_filename}-reply.gpg"
                encrypted_reply_path = Path(storage.path(source.filesystem_id, fname))
                encryption_mgr.encrypt_journalist_reply(
                    for_source=source,
                    reply_in=content,
                    encrypted_reply_path_out=encrypted_reply_path,
                )

                # Save encrypted item if flag is set
                if save_items:
                    saved_item_path = items_dir / f"{uuid}.gpg"
                    shutil.copy2(encrypted_reply_path, saved_item_path)

                # Override with pre-encrypted file if specified in YAML
                if "encrypted_file" in item_data:
                    pre_encrypted_path = yaml_dir / item_data["encrypted_file"]
                    shutil.copy2(pre_encrypted_path, encrypted_reply_path)
                    print(f"Imported reply (pre-encrypted): {fname}")
                else:
                    print(
                        f"Warning: no pre-encrypted file for reply: {fname}, may be unreproducible"
                    )
                    print(f"Imported reply: {fname}")

                reply = Reply(journalist, source, fname, storage)
                reply.uuid = uuid
                reply.deleted_by_source = item_data["deleted_by_source"]

                db.session.add(reply)
                uuid_to_reply[uuid] = reply

    db.session.commit()
    print(f"Imported {submission_count} submissions and {reply_count} replies")
    return uuid_to_submission, uuid_to_reply


def import_seen_records(
    sources_data: list[dict[str, Any]],
    uuid_to_submission: dict[str, Submission],
    uuid_to_reply: dict[str, Reply],
    uuid_to_journalist: dict[str, Journalist],
) -> None:
    """Import seen records from seen_by arrays in items."""
    seen_count = 0

    for source_data in sources_data:
        for item_data in source_data["items"]:
            uuid = item_data["uuid"]
            kind = item_data["kind"]
            seen_by_uuids = item_data["seen_by"]

            if seen_by_uuids:
                for journalist_uuid in seen_by_uuids:
                    journalist = uuid_to_journalist[journalist_uuid]

                    if kind == "message":
                        submission = uuid_to_submission[uuid]
                        seen_record = SeenMessage(message=submission, journalist=journalist)
                        db.session.add(seen_record)
                        seen_count += 1
                    elif kind == "file":
                        submission = uuid_to_submission[uuid]
                        seen_record = SeenFile(file=submission, journalist=journalist)
                        db.session.add(seen_record)
                        seen_count += 1
                    elif kind == "reply":
                        reply = uuid_to_reply[uuid]
                        seen_record = SeenReply(reply=reply, journalist=journalist)
                        db.session.add(seen_record)
                        seen_count += 1

    print(f"Created {seen_count} seen records")
    db.session.commit()


def load_fixed_data(yaml_path: Path, save_items: bool = False) -> None:
    """Load fixed test data from YAML into the database."""
    if not os.environ.get("SECUREDROP_ENV"):
        os.environ["SECUREDROP_ENV"] = "dev"

    config = SecureDropConfig.get_current()
    app = journalist_app.create_app(config)

    with app.app_context():
        print("Loading fixed data from YAML...")

        verify_empty_database()

        with yaml_path.open("r") as f:
            data = yaml.safe_load(f)
        yaml_dir = yaml_path.parent

        print("\n--- Importing journalists ---")
        uuid_to_journalist = import_journalists(data["journalists"])

        print("\n--- Importing sources ---")
        uuid_to_source = import_sources(data["sources"], yaml_dir)

        print("\n--- Importing items (messages, files, and replies) ---")
        uuid_to_submission, uuid_to_reply = import_submissions_and_replies(
            data["sources"], uuid_to_source, uuid_to_journalist, yaml_dir, save_items
        )

        print("\n--- Importing seen records ---")
        import_seen_records(data["sources"], uuid_to_submission, uuid_to_reply, uuid_to_journalist)

        print("\n✓ Successfully imported fixed data:")
        print(f"  - {len(uuid_to_journalist)} journalists")
        print(f"  - {len(uuid_to_source)} sources")
        print(f"  - {len(uuid_to_submission)} submissions")
        print(f"  - {len(uuid_to_reply)} replies")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        Path(__file__).name,
        description="Loads fixed test data from a YAML file into the database",
    )
    parser.add_argument(
        "--yaml-path",
        type=Path,
        required=True,
        help="Path to the YAML data file",
    )
    parser.add_argument(
        "--save-items",
        action="store_true",
        help="Save encrypted items to items/ directory for future reproducible imports",
    )

    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = parse_arguments()
    load_fixed_data(args.yaml_path, args.save_items)
