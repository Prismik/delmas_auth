# Installation

## Python version

You should install python 2.7 on your machine. If you are not sure how to do that
we recommend that you go to [this link](https://www.python.org/download/releases/2.7/).

## PIP

PIP is a package manager for python. You will need it in order to install any
3rd party packages (the equivalent of a dll but for pytnon). PIP is installed
by default when you install python with the [provided link](https://www.python.org/download/releases/2.7/).

## Flask

Flask is a web server (just like express for Node, Sinatra for Ruby, etc.). We use
it to handle our HTTP calls and routes. To install it, simply use `pip install flask`
in your terminal.

We also use Flask-login to handle sessions persistance and login features. To install it,
simple use `pip install flask-login` in your terminal.

# Nobody expects the Spanish Inquisition!

You are good to go, simply navigate to the root of the project and run python
on index.py. Normally, python should be installed as to let you run `python2 index.py`.
