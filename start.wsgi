def application(environ, start_response):
    status = '200 OK'
    output = 'This is my Web Application!'

    response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    #return bytearray([output])
    return [output.encode('utf-8')]
