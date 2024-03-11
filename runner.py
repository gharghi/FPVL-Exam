# wsgi.py

from bot import main

def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]  # HTTP Headers
    start_response(status, headers)

    main()

    response_body = 'Running'
    return [response_body.encode('utf-8')]