
import os
import flask
from flask import Flask
from flask import render_template
from flask import request,redirect
import subprocess
import time

app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main_page_template.html')

@app.route('/', methods=['POST'])
def my_form_post():

    text = request.form['text']
    print "Getting called" + text
    return redirect("/hello/"+text)
    
@app.route("/hello")
def hello_world():
   return "<marquee>Hello World!</marquee>"

@app.route('/hello/<name>')
def every_page(name):
    string = "<h1>Welcome to the <i><u>%s</i></u> page!<h1>" % name
    string += '<h3><a href="/">Back to main page</a><h3><br><hr><br>'
    string += '<iframe height=1000 width=1000 src="https://www.bing.com/images/search?q=' + name + '"></iframe>'

    return string

@app.route('/match') # This lets us run command line stuff and have it do cool stuff
def index():
    def inner():
        proc = subprocess.Popen(
            ['python match.py'],
            shell=True,
            stdout=subprocess.PIPE
        )

        for line in iter(proc.stdout.readline,''):
            time.sleep(1)                           # Don't need this just shows the text streaming
            yield line.rstrip() + '<br/>\n'

    return flask.Response(inner(), mimetype='text/html')  # text/html is required for most browsers to show th

app.debug = True # This makes all the stuff pretty. Now it auto-restarts for code changes.
# (No more "Dylan restart plz I have problems")
app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))