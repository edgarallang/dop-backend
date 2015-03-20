from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return "Hello World! I'm using python with flask fuck yeah!"

if __name__ == '__main__':
    app.run()