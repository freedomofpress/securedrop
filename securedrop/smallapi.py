from flask import url_for, current_app
import datetime
from collections import defaultdict
from db import db
from sqlalchemy import text


def get_all_sources():
    sql = text("SELECT filename, source_id FROM submissions")
    results = db.engine.execute(sql)

    # A dictionary of all source_ids and their submission names in a list as value
    submissions = defaultdict(list)
    for res in results:
        submissions[res["source_id"]].append(res["filename"])

    sql = text("SELECT source_id, starred FROM source_stars")
    results = db.engine.execute(sql)

    stars = {res["source_id"]: res["starred"] for res in results}

    sql = text(
        "SELECT id, uuid, filesystem_id, journalist_designation, flagged,"
        "last_updated, pending, interaction_count FROM sources"
    )
    sources = db.engine.execute(sql)

    # this is the final result list
    result = []
    for source in sources:
        source_id = source["id"]
        if source["last_updated"]:
            timestamp = source["last_updated"] + "Z"
        else:
            timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        starred = False
        if source_id in stars:
            starred = bool(stars[source_id])

        messages = 0
        documents = 0

        subs = submissions.get(source_id, [])
        for sub in subs:
            if sub.endswith("msg.gpg"):
                messages += 1
            elif sub.endswith("doc.gz.gpg") or sub.endswith("doc.zip.gpg"):
                documents += 1

        json_source = {
            "uuid": source["uuid"],
            "url": url_for("api.single_source", source_uuid=source["uuid"]),
            "journalist_designation": source["journalist_designation"],
            "is_flagged": source["flagged"],
            "is_starred": starred,
            "last_updated": timestamp,
            "interaction_count": source["interaction_count"],
            "key": {
                "type": "PGP",
                "public": current_app.crypto_util.get_pubkey(source["filesystem_id"]),
                "fingerprint": current_app.crypto_util.get_fingerprint(
                    source["filesystem_id"]
                ),
            },
            "number_of_documents": documents,
            "number_of_messages": messages,
            "submissions_url": url_for(
                "api.all_source_submissions", source_uuid=source["uuid"]
            ),
            "add_star_url": url_for("api.add_star", source_uuid=source["uuid"]),
            "remove_star_url": url_for("api.remove_star", source_uuid=source["uuid"]),
            "replies_url": url_for(
                "api.all_source_replies", source_uuid=source["uuid"]
            ),
        }
        result.append(json_source)
    return result
