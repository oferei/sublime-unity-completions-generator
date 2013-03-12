from writer_base import WriterBase

import os

class WriterSnippets(WriterBase):

	SNIPPET_FILE_FORMAT = "<snippet>\n" \
		"\t<content><![CDATA[%s]]></content>\n" \
		"\t<tabTrigger><![CDATA[%s]]></tabTrigger>\n" \
		"\t<scope>%s</scope>\n" \
		"\t<description><![CDATA[%s]]></description>\n" \
		"</snippet>\n"

	def __init__(self, outDir, name, scopeName):
		self.name = name
		self.scopeName = scopeName
		self.outDir = os.path.join(outDir, self.name)
		if not os.path.isdir(self.outDir):
			os.makedirs(self.outDir)
		self.sectionDir = self.outDir
		self.shortFilenames = {}

	def terminate(self):
		pass

	def writeHeader(self, scopeName):
		pass

	def writeFooter(self):
		pass

	def startSection(self, sectionName):
		self.sectionDir = os.path.join(self.outDir, sectionName)
		if not os.path.isdir(self.sectionDir):
			os.makedirs(self.sectionDir)

	def endSection(self):
		self.sectionDir = self.outDir

	def writeClass(self, className):
		self.writeSnipperFiles(filename=className,
								content=className,
								trigger=className,
								description='[class]')

	def writeVariable(self, className, memberName):
		self.writeSnipperFiles(filename=className + '_' + memberName + '_class',
								content=className + '.' + memberName,
								trigger=className + '.' + memberName,
								description='[var]')
		self.writeSnipperFiles(filename=className + '_' + memberName + '_var',
								content=className + '.' + memberName,
								trigger=memberName,
								description=className + '.*')

	def writeFunction(self, funcName, template, paramNames, contents):
		if '.' in funcName:
			className, memberName = funcName.split('.', 1)
			self.writeSnipperFiles(filename=funcName + template + '(' + paramNames + ')_class',
									content=contents,
									trigger=className + '.' + memberName,
									description='*' + template + '(' + paramNames + ')')
			self.writeSnipperFiles(filename=funcName + template + '(' + paramNames + ')_func',
									content=contents,
									trigger=memberName,
									description=className + '.*' + template + '(' + paramNames + ')')
		else:
			self.writeSnipperFiles(filename=funcName + template + '(' + paramNames + ')',
									content=contents,
									trigger=funcName,
									description='*' + template + '(' + paramNames + ')')

	def writeSnipperFiles(self, filename, content, trigger, description):
		self.writeSnipperFile(filename, content, trigger, description)
		if trigger[0].isupper():
			self.writeSnipperFile(filename + '_lower', content, trigger[0].lower() + trigger[1:], description)

	def writeSnipperFile(self, filename, content, trigger, description):
		filename = filename.replace('<', '[').replace('>', ']').replace(' ', '_')
		filename = self.getShortFilename(filename)
		file = open(os.path.join(self.sectionDir, '%s.sublime-snippet' % filename), 'w')
		file.write(self.SNIPPET_FILE_FORMAT % (content, trigger, self.scopeName, description))

	MAX_FILENAME = 100
	POSTFIX_MAX_SIZE = 6
	def getShortFilename(self, filename):
		if len(filename) < self.MAX_FILENAME - self.POSTFIX_MAX_SIZE:
			return filename
		short = filename[:self.MAX_FILENAME - self.POSTFIX_MAX_SIZE]
		self.shortFilenames[short] = self.shortFilenames.setdefault(short, 0) + 1
		return short + '_' + str(self.shortFilenames[short])
