import sqlite3
import json
import flask

def run_meta_query(sql):
  with sqlite3.connect('studio.db') as db:
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute(sql)
    return [dict(x) for x in c.fetchall()]

def get_folio(name):
  with sqlite3.connect('studio.db') as db:
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('''
    select name, prompt, query, params
      from folios
     where name = ?
    ''', (name,))
    v = dict(c.fetchone())
    v['params'] = json.loads(v['params'])
    return v

def insert_folio(name, prompt):
  with sqlite3.connect('studio.db') as db:
    c = db.cursor()
    c.execute('''
    insert into folios (name, prompt, query, params)
      values (?, ?, 'select * from table;', '{}')
    ''', (name, prompt))

def update_folio(name, rename, prompt, query, params):
  with sqlite3.connect('studio.db') as db:
    c = db.cursor()
    c.execute('''
    update folios
       set name = ?,
           prompt = ?,
           query = ?,
           params = ?
     where name = ?
    ''', (rename, prompt, query, params, name))

app = flask.Flask(__name__)

@app.route("/")
def index():
  return flask.render_template('index.html', folios = run_meta_query('select * from folios'))

@app.route("/folios", methods=['POST'])
def post_folios():
  attrs = flask.request.get_json()
  insert_folio(attrs['name'], attrs['prompt'])
  return ('', 202)

@app.route("/folio/<name>", methods=['PUT', 'GET'])
def put_folio(name):
  if flask.request.method == 'PUT':
    attrs = flask.request.get_json()
    update_folio(name, attrs['name'], attrs['prompt'], attrs['query'], json.dumps(attrs['params']))
    return ('', 204)
  else:
    return get_folio(name)

@app.route("/q", methods=['POST'])
def run_data_query():
  attrs = flask.request.get_json()
  try:
    return {
      'status': 'ok',
      'data': run_meta_query(attrs['sql']),
    }
  except Exception as e:
    return {
      'status': 'error',
      'error': 'There was a problem with your SQL query',
      'exception': str(e)
    }
