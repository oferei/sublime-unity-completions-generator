from writer_base import WriterBase

import os

class WriterCompletions(WriterBase):
	OUTPUT_FILENAME = 'Unity.%s.sublime-completions'

	FILE_HEADER = "{\n\t\"scope\": \"%s\",\n\n\t\"completions\":\n\t[\n"
	SECTION_START_LINE = "\t\t// %s\n"
	SECTION_END_LINE = "\n"
	TRIGGER_LINE = "\t\t{ \"trigger\": \"%s\", \"contents\": \"%s\" },\n"
	FILE_FOOTER = "\t\t{}\n\t]\n}\n"

	def __init__(self, outDir, name, scopeName):
		self.name = name
		if not os.path.isdir(outDir):
			os.makedirs(outDir)
		self.file = open(os.path.join(outDir, self.OUTPUT_FILENAME % name), 'w')
		self.writeHeader(scopeName)

	def terminate(self):
		self.writeFooter()

	def writeHeader(self, scopeName):
		self.file.write(self.FILE_HEADER % scopeName)

	def writeFooter(self):
		self.file.write(self.FILE_FOOTER)

	def startSection(self, sectionName):
		self.file.write(self.SECTION_START_LINE % sectionName)

	def endSection(self):
		self.file.write(self.SECTION_END_LINE)

	def writeClass(self, className):
		self.file.write(self.TRIGGER_LINE % (className, className))

	def writeVariable(self, className, memberName):
		self.file.write(self.TRIGGER_LINE % (className + '.' + memberName, className + '.' + memberName))

	def writeFunction(self, funcName, template, paramNames, contents):
		trigger = funcName + template + '(' + paramNames + ')'
		self.file.write(self.TRIGGER_LINE % (trigger, contents))
