# Copyright 2014 Mitchell Kember. Subject to the MIT License.

"""Implements the server for the web application."""

import gevent
import os.path
import webbrowser
from datetime import datetime
from gevent import pywsgi
from sys import exit

from scribbler.controller import Controller


# Response statuses.
STATUS_200 = '200 OK'
STATUS_204 = '204 NO CONTENT'
STATUS_404 = '404 NOT FOUND'

# MIME types for file extensions.
MIME_PLAIN = 'text/plain'
MIMES = {'html': 'text/html', 'css': 'text/css', 'js': 'application/javascript'}

# Convential paths for important files.
PATH_INDEX = '/index.html'
PATH_404 = '/404.html'


class Server(object):

    """A very simple web server."""

    def __init__(self, host, port, root, whitelist):
        """Create a server that serves from root on host:port.

        Only paths in the root directory that are also present in the whitelist
        will be served. The whitelist paths are absolute, so they must begin
        with a slash. The paths '/', '/index.html', and '/404.html' must be
        included for the website to work properly.
        """
        self.httpd = pywsgi.WSGIServer((host, port), self.handle_request)
        self.url = "http://{}:{}".format(host, port)
        self.root = root.rstrip('/')
        self.whitelist = whitelist
        self.running = False
        self.controller = Controller()

    def start(self, open_browser=True, verbose=True):
        """Starts the server if it is not already running. Unless False
        arguments are passed, prints a message to standard output and opens the
        browser to the served page."""
        if self.running:
            return
        self.httpd.start()
        if verbose:
            print("Serving on {}...".format(self.url))
        if open_browser:
            webbrowser.open(self.url)
        self.running = True

    def stop(self):
        """Stops the program and the server. Does nothing if already stopped."""
        if self.running:
            self.controller.stop()
            self.httpd.stop()

    def stay_alive(self):
        """Prevents the program from ending by never returning. Only exits when
        a keyboard interrupt is detected. The server must already be running."""
        assert self.running
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            exit()

    def handle_request(self, env, start_response):
        """Handles all server requests."""
        method = env['REQUEST_METHOD']
        if method == 'GET':
            return self.handle_get(env['PATH_INFO'], start_response)
        elif method == 'POST':
            return self.handle_post(extract_data(env), start_response)

    def handle_get(self, path_info, start_response):
        """Handles a GET request, which is used for getting resources."""
        path = self.path(path_info)
        head = headers(get_mime(path), os.path.getsize(path))
        start_response(get_status(path), head)
        return open(path)

    def handle_post(self, data, start_response):
        """Handles a POST request, which is used for AJAX communication."""
        msg = self.controller(data)
        if msg == None:
            head = headers(get_mime(), 0)
            start_response(STATUS_204, head)
            return [None]
        head = headers(get_mime(), len(msg))
        start_response(get_status(), head)
        return [msg]

    def path(self, path_info):
        """Returns the relative path that should be followed for the request.
        The root will go to index file. Anything not present in the server's
        whitelist will cause a 404."""
        if path_info in self.whitelist:
            if path_info == '/':
                path_info = PATH_INDEX
        else:
            path_info = PATH_404
        return self.root + path_info


def get_status(path=None):
    """Returns the request status to use for the given path. Defaults to 200 if
    no argument is passed."""
    if path == PATH_404:
        return STATUS_404
    return STATUS_200


def get_mime(path=None):
    """Returns the MIME type to use for the given path. Defaults to 'text/plain'
    if the extension is not recognized, or if no argument is passed."""
    if not path:
        return MIME_PLAIN
    _, ext = os.path.splitext(path)
    without_dot = ext[1:]
    return MIMES.get(without_dot, MIME_PLAIN)


def headers(mime, length):
    """Returns a list of HTTP headers given the MIME type and the length of the
    content, in bytes (in integer or sting format)."""
    return [('Content-Type', mime),
            ('Content-Length', str(length))]


def extract_data(env):
    """Extracts the data from the envment of a POST request."""
    try:
        length = int(env.get('CONTENT_LENGTH', '0'))
    except ValueError:
        length = 0
    if length != 0:
        return env['wsgi.input'].read(length)
    return ""
