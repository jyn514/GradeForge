#!/usr/bin/env python3
import flask
from ..sql import query

app = flask.Flask(__name__, template_folder='.', static_url_path='/')

@app.route('/', methods=['GET'])
@app.route('/index.html', methods=['GET'])
@app.route('/courses.html', methods=['GET'])
def main():
    return flask.render_template('index.html')


@app.route('/sections.html', methods=['GET', 'POST'])
def submit():
    params = (flask.request.args if flask.request.method == 'GET' else flask.request.form)
    print(params) # TODO
    return flask.redirect('/') # also TODO


@app.route('/api.json', methods=['GET', 'POST'])
@app.route('/api.html', methods=['GET', 'POST'])
@app.route('/api', methods=['GET', 'POST'])
def sections():
    params = (flask.request.args if flask.request.method == 'GET' else flask.request.form)
    response = flask.make_response(query(**params))  # TODO
    # don't cache anything: https://stackoverflow.com/a/2068407
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/favicon.png', methods=['GET'])
def favicon():
    return flask.send_from_directory('.', 'favicon.png')
