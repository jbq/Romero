import os.path, StringIO, sys, operator, datetime
class App:
	def __init__(self, environ, start_response):
		self.root = os.path.join(environ['DOCUMENT_ROOT'], "..")
		self.imagepath = os.path.join(environ['DOCUMENT_ROOT'], 'images')
		self.environ = environ
		self._startResponse = start_response
		self.status = "200 OK"
		self.headers = []

	def addHeader(self, name, value):
		self.headers.append((name, value))

	def handleRequest(self):
		try:
			value = self.processRequest()
			self._startResponse(self.status, self.headers)	
			return value
		except:
			import cgitb
			self._startResponse("500 Internal Server Error", [('Content-Type', 'text/html')])
			return cgitb.html(sys.exc_info())

	def makeimagepath(self, path):
		p = os.path.abspath(os.path.join(self.imagepath, path))
		if not p.startswith(self.imagepath):
			raise Exception("Wrong path: %s" % path)
		return p

	def image(self, path, w, h):
		import PIL.Image
		type = "jpeg"
		s = StringIO.StringIO()
		im = PIL.Image.open(self.makeimagepath(path[1:]))
		im.convert('RGB')
		im.thumbnail((w, h), PIL.Image.ANTIALIAS)
		im.save(s, type)
		self.addHeader("Content-Type", "image/%s" % type)
		return s.getvalue()

	def top10(self):
		dirs = [(f, datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(self.imagepath, f)))) for f in os.listdir(self.imagepath) if os.path.isdir(os.path.join(self.imagepath, f)) and not f.startswith(".")]
		return sorted(dirs, key=operator.itemgetter(1))[:10]

	def pictures(self, path):
		path = self.makeimagepath(path)
		return sorted([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and not f.startswith(".")])

	def sequences(self, path):
		path = self.makeimagepath(path)
		return sorted([f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f)) and not f.startswith(".")])

	def previous(self, path, offset=-1):
		pics = self.pictures(os.path.dirname(path))
		idx = pics.index(os.path.basename(path)) 
		if idx == 0 and offset == -1:
			return None
		try:
			return pics[idx + offset]
		except IndexError:
			return None

	def first(self, path):
		pics = self.pictures(os.path.dirname(path))
		idx = pics.index(os.path.basename(path)) 
		if idx == 0:
			return None
		return pics[0]

	def last(self, path):
		pics = self.pictures(os.path.dirname(path))
		idx = pics.index(os.path.basename(path)) 
		if idx == len(pics) - 1:
			return None
		return pics[-1]

	def next(self, path):
		return self.previous(path, offset=1)

	def processRequest(self):
		uri = self.environ['PATH_INFO']
		import Cheetah.Template
		if uri == "/":
			template=Cheetah.Template.Template(file=os.path.join(self.root, "templates/index.tmpl"))
			template.top10 = self.top10()
			self.addHeader("Content-Type", "text/html")
			return unicode(template).encode('utf-8')
		if uri.startswith("/thumbnail/"):
			path = uri.replace("/thumbnail", "")
			return self.image(path, 64, 48)
		if uri.startswith("/scaled/"):
			path = uri.replace("/scaled", "")
			return self.image(path, 640, 480)
		if uri.startswith("/sequence/") and uri.endswith("/"):
			path = uri.replace("/sequence", "")
			template=Cheetah.Template.Template(file=os.path.join(self.root, "templates/sequence.tmpl"))
			template.pathname = path[1:-1]
			template.pictures = self.pictures(template.pathname)
			template.sequences = self.sequences(template.pathname)
			self.addHeader("Content-Type", "text/html")
			return unicode(template).encode('utf-8')
		if uri.startswith("/sequence/"):
			path = uri.replace("/sequence", "")
			template=Cheetah.Template.Template(file=os.path.join(self.root, "templates/image.tmpl"))
			template.sequence = os.path.dirname(path[1:])
			template.picture = path[1:]
			template.previous = self.previous(template.picture)
			template.next = self.next(template.picture)
			template.first = self.first(template.picture)
			template.last = self.last(template.picture)
			self.addHeader("Content-Type", "text/html")
			return unicode(template).encode('utf-8')
		raise Exception("No controller for %s.  Environ: %s" % (uri, repr(self.environ)))

def application(environ, start_response):
	app = App(environ, start_response)
	return app.handleRequest()
