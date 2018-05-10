#!/bin/python3
# HTTP server
import http.server as httpsrv
import os
#import socketserver

PORT = 8000

# Process the User Response.
def processResponse(response):
  response = response.strip("'b") + "&"
  # Change these to provide things back to the user.
  split = response.strip("'b").split("&")
  os.system("../jpc/grades.sh " + "'" + response + "'")
  prefix = split[0].split("=")[1]
  courseNumber = split[1].split("=")[1]
  section = split[2].split("=")[1]
  imgPath = "./test.png"
  return (prefix,courseNumber, section, imgPath)

class RequestHandler(httpsrv.BaseHTTPRequestHandler):
  #rfile in input
  #wfile is output
  
  # Do Normal Headers
  def _do_headers(self):
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    
  # Do Headers if File is Not Found  
  def _do_FileNotFound(self):
    self.send_response(404)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    
  #Override the GET Function for handling form submissions
  def do_GET(self):
    #print("Doing GET...")
    #print("WFILE: " + str(self.wfile))
    isBinary = False
    path = str(self.path)
    if path == "/":
      path = "/index.html"
    #print("Path is: " + path)
    toReturn = "404: File not Found"
    try:
      f = open(path[1:], "r")
      toReturn = f.read()
      self._do_headers()
    except UnicodeDecodeError:
      # Attempt to Read file as a binary
      try:
        #print("Reading " + path + " as binary...")
        f = open(path[1:], "rb")
        toReturn = f.read()
        self._do_headers()
        isBinary = True
      except IOError: #For sanity
        self._do_FileNotFound()
        print("File [" + str(path) + "] Not Found!")
    except IOError:
      self._do_FileNotFound()
      print("File [" + str(path) + "] Not Found!")
    #print("IS BINARY: " + str(isBinary))
    if isBinary:
      self.wfile.write(toReturn)
    else:
      self.wfile.write(toReturn.encode("utf-8"))
  
  # Handle a POST Request (After user fills in the form
  def do_POST(self):
    #self._do_headers()
    #print("Doing POST..")
    #print("Path is: " + str(self.path))
    #print("WFILE: " + str(self.wfile))
    path = str(self.path)
    toReturn = "[POST] 404: File not Found"
    try:
      f = open(path[1:], "r")
      toReturn = f.read()
      self._do_headers()
    except IOError:
      self._do_FileNotFound()
      print("File [" + str(path) + "] Not Found!")
    #Read from POST Request
    post = str(self.rfile.read(int(self.headers['Content-Length'])))[:]
    #print("POST: " + post)
    (prefix,courseNumber, section, imgPath) = processResponse(post)
    toReturn = toReturn.replace("{PREFIX}",prefix)
    toReturn = toReturn.replace("{COURSE_NUMBER}",courseNumber)
    toReturn = toReturn.replace("{SECTION}", section)
    toReturn = toReturn.replace("{IMG_PATH}", imgPath)
    #print("HTML:\n" + toReturn + "===\n")
    #self.wfile.write("POST Request:\n".encode("utf-8"))
    self.wfile.write(toReturn.encode("utf-8"))

#Handler = httpsrv.SimpleHTTPRequestHandler
Handler = RequestHandler
#Serves the HTTP things
h = httpsrv.HTTPServer(("127.0.0.1",PORT),Handler)
print("Serving HTTP...")
h.serve_forever()
print("Never goes Here!")
