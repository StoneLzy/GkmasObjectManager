"""
server.py
Flask web server entry point.
"""

from datetime import datetime, timedelta, timezone

from flask import Flask, Response, jsonify, render_template, request

import GkmasObjectManager as gom
from GkmasObjectManager.manifest import GkmasManifest

app = Flask(__name__)
m = None


def _get_manifest() -> GkmasManifest:
    global m
    if m is None:
        m = gom.fetch()
    return m


def _sanitize_mtime(mtime: float) -> str:
    mtime = datetime.fromtimestamp(mtime, tz=timezone.utc)
    mtime = mtime.astimezone(timezone(timedelta(hours=9)))  # Japan Standard Time
    return mtime.strftime("%Y-%m-%d %H:%M:%S")


# API endpoints


@app.route("/api/manifest")
def api_manifest() -> Response:
    return jsonify(_get_manifest()._get_canon_repr())


@app.route("/api/search")
def api_search() -> Response:
    query = request.args.get("query", "")
    return jsonify(
        [
            {
                "id": obj.id,
                "name": obj.name,
                "type": type(obj).__name__[5:],  # valid names start with "Gkmas"
            }
            for obj in _get_manifest().search(
                "".join(f"(?=.*{word})" for word in query.split())
                # use lookahead to match all words in any order
            )
        ]
    )


@app.route("/api/<type>/<id>/bytestream")
def api_bytestream(type: str, id: str) -> Response:

    try:
        obj = getattr(_get_manifest(), f"{type.lower()}s")[int(id)]
    except (AttributeError, KeyError):
        return jsonify({"error": "Object not found"})

    data = obj.get_data()
    return Response(
        data["bytes"],
        mimetype=data["mimetype"],
        headers={"Last-Modified": _sanitize_mtime(data["mtime"])},
    )


# Frontend routes


@app.route("/")
def home() -> str:
    return render_template("home.html")


@app.route("/search")
def search() -> str:
    return render_template(
        "search.html",
        query=request.args.get("query", ""),
        byID=request.args.get("byID", "true") == "true",
        ascending=request.args.get("ascending", "false") == "true",
        entriesPerPage=int(request.args.get("entriesPerPage", 12)),
        currentPage=int(request.args.get("currentPage", 1)),
    )


@app.route("/view/<type>/<id>")
def view(type: str, id: str) -> str:

    if type == "assetbundle":
        type_display = "AssetBundle"
    elif type == "resource":
        type_display = "Resource"
    else:
        return render_template("404.html")

    try:
        obj = getattr(_get_manifest(), f"{type.lower()}s")[int(id)]
    except (AttributeError, KeyError):
        return render_template("404.html")

    info = obj._get_canon_repr()
    info["raw_url"] = obj._url
    if "dependencies" in info:
        info["dependencies"] = [
            {
                "id": dep,
                "name": getattr(_get_manifest(), f"{type.lower()}s")[int(dep)].name,
            }
            for dep in info["dependencies"]
        ]

    return render_template("view.html", info=info, type=type_display)


@app.errorhandler(404)
def page_not_found(error: Exception) -> tuple[str, int]:
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5001)
