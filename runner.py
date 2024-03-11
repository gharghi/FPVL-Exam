# runner.py

import sys

# Add the directory where bot.py is located to the Python path
sys.path.insert(0, '/home/behroozitest/voar')

from bot import main

def application(environ, start_response):
    """A simple WSGI application."""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)

    # Call the main function from bot.py and get the response
    response = main()

    # Convert the response to a bytes object
    response_bytes = response.encode('utf-8')

    return [response_bytes]
