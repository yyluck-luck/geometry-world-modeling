"""One public arXiv metadata query, preserving raw response and actual outcome.

Metadata discovery only: read the paper and verify its official venue separately.
See https://info.arxiv.org/help/api/user-manual.html . No credentials required.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help='For example: ti:"History-Guided Video Diffusion"')
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-results", default=3, type=int, choices=range(1, 21))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": args.query, "start": 0, "max_results": args.max_results}
    )
    receipt = {"started_utc": datetime.now(timezone.utc).isoformat(), "url": url,
               "query": args.query, "entries": [], "status": "NOT_COMPLETED",
               "scope": "Public metadata retrieval, not paper reading or venue verification"}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "geometry-research-metadata/1.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read()
            receipt["http_status"] = response.status
        (args.output / "response.xml").write_bytes(body)
        receipt["response_sha256"] = hashlib.sha256(body).hexdigest()
        receipt["response_bytes"] = len(body)
        ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
        tree = ET.fromstring(body)
        if tree.tag != "{http://www.w3.org/2005/Atom}feed":
            raise ValueError("Response is not an Atom feed")
        for item in tree.findall("a:entry", ns):
            record = {key: " ".join((item.findtext("a:" + key, default="", namespaces=ns)).split())
                      for key in ["id", "title", "published", "updated", "summary"]}
            if "/api/errors" in record["id"]:
                raise ValueError(record["summary"])
            record["authors"] = [a.findtext("a:name", namespaces=ns) for a in item.findall("a:author", ns)]
            record["links"] = [dict(e.attrib) for e in item.findall("a:link", ns)]
            record["journal_reference_author_supplied"] = item.findtext("x:journal_ref", namespaces=ns)
            receipt["entries"].append(record)
        receipt["status"] = "SUCCESS" if receipt["entries"] else "SUCCESS_NO_MATCHES"
    except Exception as error:
        receipt["status"] = "FAILED"
        receipt["error_type"] = type(error).__name__
        receipt["error"] = str(error)
        if isinstance(error, urllib.error.HTTPError):
            receipt["http_status"] = error.code
            (args.output / "error_response.txt").write_bytes(error.read())
    receipt["completed_utc"] = datetime.now(timezone.utc).isoformat()
    (args.output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False))
    return 1 if receipt["status"] == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
