import os
import csv
import datetime
import statistics
import uuid

import flask


app = flask.Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(
        os.path.join(app.root_path, 'static'),
        "favicon.ico"
    )


@app.route("/")
def questions():
    with open("items.txt", "r") as open_file:
        lines = open_file.read().splitlines()
    items = [
        {"index": index, "item": line}
        for index, line in enumerate(lines, 1)
    ]
    new_session = {
        "session_id": uuid.uuid4().hex,
        "start": f'{datetime.datetime.now():%x_%X}'
    }
    with open("scores.csv", "a+") as open_file:
        writer = csv.DictWriter(open_file, fieldnames=new_session.keys())
        writer.writerow(new_session)
    return flask.render_template(
        "questions.html",
        questions=items,
        session_id=new_session["session_id"]
    )


@app.route("/result", methods=["POST", "GET"])
def result():
    if flask.request.method == "POST":
        session_id = flask.request.form.get("session_id")
        score = 100-list(flask.request.form.values()).count("on")
        scores = [
            int(row["score"]) for row in record(session_id, score)
            if "score" in row.keys()
        ]
        average = f'{statistics.mean(scores):.1f}'
        median = f'{statistics.median(scores):.1f}'
        return flask.render_template(
            "result.html",
            result=str(score),
            average=average,
            median=median
        )
    elif flask.request.method == "GET":
        return flask.redirect("/")


def record(session_id: str, score: int) -> list[int]:
    with open("scores.csv", "r") as open_file:
        rows = list(csv.DictReader(open_file))
    rows = validate_session(rows, session_id, score)
    with open("scores.csv", "w") as open_file:
        writer = csv.DictWriter(open_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return rows


def validate_session(
    rows: list[dict[str, str]],
    session_id: str,
    score: str
) -> list[dict[str, str]]:
    session_rows = [row for row in rows if row.get("session_id") == session_id]
    if len(session_rows) == 1:
        session_rows[0].update({
            "stop": f'{datetime.datetime.now():%x_%X}',
            "score": score
        })
        start = datetime.datetime.strptime(session_rows[0]["start"], "%x_%X")
        stop = datetime.datetime.strptime(session_rows[0]["stop"], "%x_%X")
        if (stop-start).total_seconds() < 30:
            rows.remove(session_rows[0])
    return [row for row in rows if all(row.values())]
