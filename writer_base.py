class WriterBase(object):
	def __init__(self, outDir, name, scopeName):
		raise NotImplementedError

	def writeHeader(self):
		raise NotImplementedError

	def writeFooter(self):
		raise NotImplementedError

	def startSection(self, sectionName):
		raise NotImplementedError

	def endSection(self):
		raise NotImplementedError

	def writeClass(self, className):
		raise NotImplementedError

	def writeVariable(self, className, memberName):
		raise NotImplementedError

	def writeFunction(self, funcName, template, paramNames, contents):
		raise NotImplementedError
