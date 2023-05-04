import os
import csv
import datetime
import statistics
import uuid
from scipy import stats

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
    with open("/home/apdapuritytest/apda_purity_test/items.txt", "r") as open_file:
        lines = open_file.read().splitlines()
    items = [
        {"index": index, "item": line}
        for index, line in enumerate(lines, 1)
    ]
    new_session = {
        "session_id": uuid.uuid4().hex,
        "start": f'{datetime.datetime.now():%x_%X}'
    }
    with open("/home/apdapuritytest/apda_purity_test/scores.csv", "a+") as open_file:
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
        percentile, scores = record(session_id, score)
        average = f'{statistics.mean(scores):.1f}'
        median = f'{statistics.median(scores):.1f}'
        return flask.render_template(
            "result.html",
            result=f'{score} - {percentile}',
            average=average,
            median=median
        )
    elif flask.request.method == "GET":
        return flask.redirect("/")


def record(session_id: str, score: int) -> tuple[float, list[int]]:
    with open("/home/apdapuritytest/apda_purity_test/scores.csv", "r") as open_file:
        rows = list(csv.DictReader(open_file))
    rows = validate_session(rows, session_id, score)
    with open("/home/apdapuritytest/apda_purity_test/scores.csv", "w") as open_file:
        writer = csv.DictWriter(open_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    all_scores = [int(row["score"]) for row in rows if "score" in row.keys()]
    return score_percentile(all_scores, score), all_scores


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
        stop = datetime.datetime.strptime(session_rows[0]["stop"], "%x_%X")
        start = datetime.datetime.strptime(session_rows[0]["start"], "%x_%X")
        if (stop-start).total_seconds() < 30:
            rows.remove(session_rows[0])
    return [row for row in rows if all(row.values()) and len(row) == 4]


def score_percentile(scores: list[int], score: int) -> str:
    percentile = stats.percentileofscore(scores, score)
    if percentile > 50:
        lower = len([low_score for low_score in scores if low_score < score])
        return f'higher than {lower}/{len(scores)} (top {101-percentile:.0f}%)'
    higher = len([high_score for high_score in scores if high_score > score])
    return f'lower than {higher}/{len(scores)} (bottom {percentile:.0f}%)'
