import json
import re
import sqlite3
import uuid

import duckdb
import flask
import markdown_it
import ollama


def run_meta_query(sql):
    with sqlite3.connect("studio.db") as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute(sql)
        return [dict(x) for x in c.fetchall()]

def run_data_query(sql):
    c = duckdb.connect()
    return c.sql(sql).df().to_dict(orient='records')

def first(c):
    v = c.fetchone()
    if v is None:
        return None
    return dict(v)


def get_folios():
    with sqlite3.connect("studio.db") as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute(
            """
    select id,
           name,
           query,
           prompt,
           params
      from folios
     where deleted_yn != 'Y'
    """
        )
        l = []
        for r in c.fetchall():
            v = dict(r)
            v["params"] = json.loads(v["params"])
            l.append(v)
        return l


def get_folio(id):
    with sqlite3.connect("studio.db") as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute(
            """
    select id, name, prompt, query, params
      from folios
     where id = ?
       and deleted_yn != 'Y'
    """,
            (id,),
        )
        v = first(c)
        if v is not None:
            v["params"] = json.loads(v["params"])
        return v


def insert_folio(name, prompt):
    id = str(uuid.uuid4())
    with sqlite3.connect("studio.db") as db:
        c = db.cursor()
        c.execute(
            """
    insert into folios (id, name, prompt, query, params)
      values (?, ?, ?, 'select * from table;', '{}')
    """,
            (id, name, prompt),
        )
        return id


def update_folio(id, name, prompt, query, params):
    with sqlite3.connect("studio.db") as db:
        c = db.cursor()
        c.execute(
            """
    update folios
       set name = ?,
           prompt = ?,
           query = ?,
           params = ?
     where id = ?
       and deleted_yn != 'Y'
    """,
            (name, prompt, query, params, id),
        )


def archive_folio(id):
    with sqlite3.connect("studio.db") as db:
        c = db.cursor()
        c.execute(
            """
    update folios
       set deleted_yn = 'Y'
     where id = ?
    """,
            (id,),
        )


def get_response(folio_id, data_id, prompt):
    with sqlite3.connect("studio.db") as db:
        db.row_factory = sqlite3.Row
        c = db.cursor()
        c.execute(
            """
    select response,
           generated_at
      from responses
     where folio_id = ?
       and data_id = ?
       and prompt = ?
    """,
            (folio_id, data_id, prompt),
        )
        return first(c)


def insert_response(folio_id, data_id, prompt, response):
    with sqlite3.connect("studio.db") as db:
        c = db.cursor()
        c.execute(
            """
    insert into responses (folio_id, data_id, prompt, response)
    values (?, ?, ?, ?)
    """,
            (folio_id, data_id, prompt, response),
        )


def gen_ai(model, prompt, params):
    # return '(bot is snoozing)'
    r = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], options=params)
    return r.message.content


app = flask.Flask(__name__)


@app.route("/")
def index():
    return flask.render_template("index.html", folios=get_folios())


@app.route("/folios", methods=["POST", "GET"])
def handle_folios():
    if flask.request.method == "POST":
        attrs = flask.request.get_json()
        return {"id": insert_folio(attrs["name"], attrs["prompt"])}
    elif flask.request.method == "GET":
        return {"folios": get_folios()}
    else:
        return "", 405


@app.route("/folio/<id>", methods=["PUT", "GET", "DELETE"])
def handle_folio(id):
    if flask.request.method == "PUT":
        attrs = flask.request.get_json()
        update_folio(
            id,
            attrs["name"],
            attrs["prompt"],
            attrs["query"],
            json.dumps(attrs["params"]),
        )
        return ("", 204)
    elif flask.request.method == "GET":
        return get_folio(id)
    elif flask.request.method == "DELETE":
        archive_folio(id)
        return ("", 200)
    else:
        return ("", 405)


@app.route("/q", methods=["POST"])
def handle_q():
    attrs = flask.request.get_json()
    try:
        return {
            "status": "ok",
            "data": run_data_query(attrs["sql"]),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "There was a problem with your SQL query",
            "exception": str(e),
        }


@app.route("/ai", methods=["POST"])
def handle_ai():
    attrs = flask.request.get_json()
    try:
        cache = attrs.get('cache', True)
        prev = None
        if cache:
            prev = get_response(attrs["folio_id"], attrs["data_id"], attrs["prompt"])
            if prev is not None:
                r = prev["response"]
        if prev is None:
            r = gen_ai("llama3.2", attrs["prompt"], attrs["params"] if 'params' in attrs else None)
            if cache:
                insert_response(attrs["folio_id"], attrs["data_id"], attrs["prompt"], r)
        md = markdown_it.MarkdownIt()
        return {
            "status": "ok",
            "response": {
                "md": r,
                "html": md.render(r),
            },
            "cached_at": prev["generated_at"] if cache and prev is not None else None,
        }
    except Exception as e:
        return {"status": "error", "error": "The bot acted up", "exception": str(e)}


@app.route("/manifest/<id>", methods=["GET"])
def handle_manifest(id):
  folio = get_folio(id)

  folio['tasks'] = []
  for row in run_data_query(folio['query']):
    rplca = {}
    for k in folio['params'].keys():
      p = folio['params'][k]
      if p['kind'] == 'database reference':
        rplca[k] = row[p['value']]
      elif p['kind'] == 'literal value':
        rplca[k] = p['value']
    prompt = re.sub(r'\[(.*?)\]', lambda m: rplca[m.group(1)], folio['prompt'])
    folio['tasks'].append({
      'data': row,
      'prompt': prompt,
    })

  return folio
