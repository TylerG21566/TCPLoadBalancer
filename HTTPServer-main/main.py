import socket
import threading
import os
import sys
import time
import mimetypes
from datetime import datetime
from urllib.parse import unquote

class Server:
    def __init__(self, host='localhost', port=8080, document_root='./www'):
        self.host = host
        self.port = port
        self.document_root = document_root # root directory for serving files
        '''
        socket.socket() creates a new socket using the given address family and socket type.
        socket.AF_INET is used for IPv4 addresses: AF = Address Family, INET = Internet Protocol (IPv4)
        and socket.SOCK_STREAM is used for TCP.
        '''
        # Create a TCP socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def parse_request(self, request):
        """Parse HTTP request and return method, path, headers
        
        What do HTTP requests look like?
        Example:

        GET /about.html HTTP/1.1\r\n
        Host: localhost:8080\r\n
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n
        Accept: text/html,application/xhtml+xml\r\n
        Accept-Language: en-US,en;q=0.9\r\n
        Connection: keep-alive\r\n
        \r\n

        \r\n - that's how HTTP separates lines (carriage return + line feed)

        Thus we can get can get array like the following via spliting by \r\n:
        [
            'GET /about.html HTTP/1.1',
            'Host: localhost:8080', 
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept: text/html,application/xhtml+xml',
            'Accept-Language: en-US,en;q=0.9',
            'Connection: keep-alive',
            ''  # Empty line marks end of headers
        ]
        """
        lines = request.split('\r\n')

        # If request is empty, return None values
        # and an empty dictionary for headers
        if not lines:
            return None, None, {}
        
        # Parse request line such as (GET /<path> HTTP/1.1)
        request_line = lines[0].split()
        if len(request_line) < 3: # Ensure there are at least 3 parts
            return None, None, {}
        
        method = request_line[0]  # e.g., GET
        path = request_line[1]    # e.g., /about.html
        version = request_line[2] # e.g., HTTP/1.1


        # Parse headers
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        return method, path, headers
    
    def get_content_type(self, path):
        """Return content type based on file extension"""
        # looks at the file extension and guesses the MIME type
        content_type, _ = mimetypes.guess_type(path)
        # prevent None content type
        return content_type or 'application/octet-stream'
    
    def create_response(self, status_code, status_message, headers=None, body=None):
        """Create HTTP response"""
        if headers is None:
            headers = {}

        # Add default headers
        headers.setdefault('Server', 'Python-HTTP-Server/1.0')
        headers.setdefault('Date', datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'))
        headers.setdefault('Connection', 'close')
        headers.setdefault('Content-Length', str(len(body)))

        repsonse = f"HTTP/1.1 {status_code} {status_message}\r\n"
        for key, value in headers.items():
            repsonse += f"{key}: {value}\r\n"
        repsonse += "\r\n"  # End of headers

        return repsonse.encode('utf-8') + body

        
    
    def handle_get(self, path):
        """Handle GET request"""
        # default to index.html if path is empty
        if path == '/':
            path = '/index.html'

        # Remove leading slash and decode URL
        file_path = os.path.join(self.document_root, unquote(path.lstrip('/')))

        # prevent directory traversal attacks
        if not os.path.abspath(file_path).startswith(os.path.abspath(self.document_root)):
            return self.create_response(
                403, 
                "Forbidden", 
                body=b'<h1>403 Forbidden</h1><p>Access denied.</p>'
                )

        try:
            # check if file exists
            if not os.path.exists(file_path):
                return self.create_response(
                    404, 
                    "Not Found", 
                    {'Content-Type': 'text/html'},
                    body=b'<h1>404 Not Found</h1><p>The requested resource was not found.</p>'
                )
            
            # check if file is a directory
            if os.path.isdir(file_path):
                return self.list_directory(file_path, path)
            

            # read and serve the file
            with open(file_path, 'rb') as f:
                content = f.read()
            content_type = self.get_content_type(file_path)


            headers = {
                'Content-Type': content_type,
            }

            return self.create_response(
                200, 
                "OK", 
                headers, 
                content
            )
        except Exception as e:
            print(f"Error serving file {file_path}: {e}")
            return self.create_response(500, 'Internal Server Error',
                                      {'Content-Type': 'text/html'},
                                      body=b'<h1>500 Internal Server Error</h1>')
        
    def list_directory(self, dir_path, url_path):
        """Create directory listing"""
        try:
            files = os.listdir(dir_path)
            files.sort()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for {url_path}</title>
    <style>
        body {{ font-family: Arial; margin: 40px; }}
        .file {{ margin: 5px 0; }}
        .dir {{ font-weight: bold; color: #0066cc; }}
    </style>
</head>
<body>
    <h1>Directory listing for {url_path}</h1>
    <hr>
"""
            if url_path != '/':
                parent = '/'.join(url_path.rstrip('/').split('/')[:-1]) or '/'
                html += f'<div class="file"><a href="{parent}">📁 ..</a></div>\n'

            for file in files:
                file_path = os.path.join(dir_path, file)
                if os.path.isdir(file_path):
                    html += f'<div class="file dir"><a href="{url_path.rstrip("/")}/{file}/">📁 {file}/</a></div>\n'
                else:
                    html += f'<div class="file"><a href="{url_path.rstrip("/")}/{file}">📄 {file}</a></div>\n'
            
            html += """
    <hr>
    <p><em>Python HTTP Server</em></p>
</body>
</html>"""
            return self.create_response(200, 'OK', 
                                      {'Content-Type': 'text/html; charset=utf-8'},
                                      html.encode('utf-8'))
        except Exception as e:
            print(f"Error listing directory: {e}")
            return self.create_response(500, 'Internal Server Error')
        
    def handle_post(self, path, headers, body):
        """Handle POST request"""
        # simple echo endpoint for tests

        if path == '/echo':
            response_body = f"""<!DOCTYPE html>
<html>
<head><title>POST Echo</title></head>
<body>
    <h1>POST Data Received</h1>
    <h2>Headers:</h2>
    <pre>{chr(10).join(f'{k}: {v}' for k, v in headers.items())}</pre>
    <h2>Body:</h2>
    <pre>{body}</pre>
    <a href="/">← Back to Home</a>
</body>
</html>"""
            return self.create_response(200, 'OK',
                                      {'Content-Type': 'text/html'},
                                      response_body.encode('utf-8'))

    def handle_client(self, client_socket, address):
        """Handle HTTP request from client"""
        try:
            ''' 
            Receive request data. Network data doesn't always arrive all at once. 
            A request might come in pieces.

            Chunk 1: "GET /index.html HTTP/1.1\r\nHost: loc"
            Chunk 2: "alhost:8080\r\nUser-Agent: Chrome"  
            Chunk 3: "/91.0\r\n\r\n"

            We need to keep reading until we have the complete request

            recv(1024) reads up to 1024 bytes from the socket:

            Might return less than 1024 bytes
            Might return exactly 1024 bytes
            Returns b'' (empty) when connection closes
            '''
            request_data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request_data += chunk
                if b'\r\n\r\n' in request_data:
                    break
                if len(request_data) > 8192:  # Limit request size
                    break
            if not request_data:
                return
            
            request = request_data.decode('utf-8', errors='ignore')

            # parse request
            method, path, headers = self.parse_request(request)
            if method is None or path is None:
                response = self.create_response(400, 'Bad Request',
                                                {'Content-Type': 'text/html'},
                                                body=b'<h1>400 Bad Request</h1>')
                client_socket.sendall(response)
            elif method == 'GET':
                response = self.handle_get(path)
            elif method == 'POST':
                # Extract body from POST request
                body_start = request_data.find(b'\r\n\r\n') + 4
                body = request_data[body_start:].decode('utf-8', errors='ignore')
                response = self.handle_post(path, headers, body)
            else:
                response = self.create_response(405, 'Method Not Allowed',
                                              body=b'<h1>405 Method Not Allowed</h1>')
            # Send response
            client_socket.send(response)
            # log request
            print(f"{address[0]} - {method} {path} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error handling request from {address}: {e}")
            try:
                error_response = self.create_response(500, 'Internal Server Error')
                client_socket.send(error_response)
            except:
                pass
        finally:
            client_socket.close()

    def start(self):
        """Start the server"""
        try:
            # "Claims" a specific address and port on your computer.
            self.server.bind((self.host, self.port))
            # Tells the OS "I am ready to accept incoming connections."
            self.server.listen(5)
            print(f"HTTP Server started on http://{self.host}:{self.port}")
            print(f"Document root: {os.path.abspath(self.document_root)}")
            print("Press Ctrl+C to stop the server")
            
            while True:
                '''
                Blocks (waits) until someone connects
                When a browser visits http://localhost:8080, this returns
                Returns two things:

                client_socket: Direct connection to that specific browser
                address: Who connected (IP address and port)
                '''
                client_socket, address = self.server.accept()
                
                # Handle each request in a separate thread
                thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address)
                )

                '''
                Thread will automatically die when the main program exits
                Without daemon: If you press Ctrl+C, zombie threads might keep running
                '''
                thread.daemon = True
                thread.start()
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.server.close()
            
        

if __name__ == "__main__":
    # Initialize defaults BEFORE the loop
    host = 'localhost'
    port = 8080
    document_root = './www'

    # Parse arguments
    for arg in sys.argv[1:]:
        if arg.startswith('--host='):
            host = arg.split('=', 1)[1]
        elif arg.startswith('--port='):
            port = int(arg.split('=', 1)[1])
        elif arg.startswith('--docroot='):
            document_root = arg.split('=', 1)[1]

    # Create server AFTER parsing all arguments
    server = Server(host=host, port=port, document_root=document_root)
    server.start()