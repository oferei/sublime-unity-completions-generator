#!/usr/bin/python
import pickle
import re

from writer_completions import WriterCompletions
from writer_snippets import WriterSnippets

# choose WriterSnippets (full) or WriterCompletions (light)
ChosenWriter = WriterSnippets

INPUT_FILENAME = 'unity.pkl'
OUTPUT_DIR = 'out'

UNKNOWN_PARAM_NAME = '?'

import logging
# create logger
logger = logging.getLogger('unity_gen_plugin_application')
logger.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

class LangFormatter(object):
	NAME = None
	SCOPE_NAME = None
	FUNCTION_POSTFIX = None

	def __init__(self, writerClass):
		self.writer = writerClass(OUTPUT_DIR, self.NAME, self.SCOPE_NAME)

	def terminate(self):
		self.writer.terminate()
	def startSection(self, sectionName):
		self.writer.startSection(sectionName)
	def endSection(self):
		self.writer.endSection()
	def writeClass(self, className):
		self.writer.writeClass(className)
	def writeVariable(self, className, memberName):
		self.writer.writeVariable(className, memberName)
	def writeFunction(self, funcName, template, paramNames, contents):
		self.writer.writeFunction(funcName, template, paramNames, contents)

	def formattedParam(self, param):
		return self.combineType(param['name'] or UNKNOWN_PARAM_NAME, self.convertTypeFromJS(param['type'])) + self.default(param['default'])

	def convertTypeFromJS(self, type_):
		return type_

	def combineType(self, name, type_):
		raise NotImplementedError

	def default(self, default):
		return ((' = ' + self.esacpe(default)) if default else '')

	def esacpe(self, s):
		return s.replace('"', '\\"')

	def formattedTemplate(self, template, withDollarOne):
		return template

	@classmethod
	def splitArrayType(cls, type_):
		m = re.search(r'^(.+)(\[.*\])$', type_)
		if m:
			return m.group(1), m.group(2)
		else:
			return type_, ''

	@classmethod
	def extractTemplateType(cls, template):
		m = re.search(r'^\.<(.+)>$', template)
		if not m:
			raise Exception('invalid template: ' + template)
		return m.group(1)

class BooFormatter(LangFormatter):
	NAME = 'Boo'
	SCOPE_NAME = 'source.boo'
	FUNCTION_POSTFIX = ''

	TYPE_CONVERSION = {
		'float': 'single',
		'String': 'string',
		'boolean': 'bool'
	}

	def convertTypeFromJS(self, type_):
		scalar, dim = self.splitArrayType(type_)
		if scalar in self.TYPE_CONVERSION:
			scalar = self.TYPE_CONVERSION[scalar]
		if dim:
			rank = dim.count(',') + 1
			if rank == 1:
				return '(%s)' % scalar
			else:
				return '(%s, %u)' % (scalar, rank)
		else:
			return scalar

	def combineType(self, name, type_):
		return '%s as %s' % (name, type_)

	def formattedTemplate(self, template, withDollarOne):
		templateType = self.extractTemplateType(template)
		if withDollarOne:
			return '[of ${1:%s}]' % templateType
		else:
			return '[of %s]' % templateType

class CSFormatter(LangFormatter):
	NAME = 'CS'
	SCOPE_NAME = 'source.cs'
	FUNCTION_POSTFIX = ';'

	TYPE_CONVERSION = {
		'String': 'string',
		'boolean': 'bool'
	}

	def convertTypeFromJS(self, type_):
		scalar, dim = self.splitArrayType(type_)
		if scalar in self.TYPE_CONVERSION:
			scalar = self.TYPE_CONVERSION[scalar]
		return scalar + dim
	
	def combineType(self, name, type_):
		return '%s %s' % (type_, name)

	def formattedTemplate(self, template, withDollarOne):
		templateType = self.extractTemplateType(template)
		if withDollarOne:
			return '<${1:%s}>' % templateType
		else:
			return '<%s>' % templateType

class JSFormatter(LangFormatter):
	NAME = 'JavaScript'
	SCOPE_NAME = 'source.js'
	FUNCTION_POSTFIX = ';'

	def combineType(self, name, type_):
		return '%s : %s' % (name, type_)

	def formattedTemplate(self, template, withDollarOne):
		templateType = self.extractTemplateType(template)
		if withDollarOne:
			return '.<${1:%s}>' % templateType
		else:
			return '.<%s>' % templateType


data = pickle.load(open(INPUT_FILENAME, 'rb'))
formatters = [f(ChosenWriter) for f in (BooFormatter, CSFormatter, JSFormatter)]

for sectionName, sectionClasses in data.iteritems():
	logger.info(sectionName)
	for f in formatters:
		f.startSection(sectionName)
	for className, classMembers in sectionClasses.iteritems():
		logger.info('    ' + className+ ' [class]')
		for f in formatters:
			f.writeClass(className)
		for memberName, funcDefs in classMembers.iteritems():
			if funcDefs is None: # variable
				logger.info('    ' + className + '.' + memberName + ' [variable]')
				for f in formatters:
					f.writeVariable(className, memberName)
			else: # function
				for funcDef in funcDefs:
					paramNames = ', '.join([param['name'] or UNKNOWN_PARAM_NAME for param in funcDef['params']])
					logger.info('    ' + className + '.' + memberName + '(' + paramNames + ') [function]')
					funcName = (className + '.' + memberName) if className != memberName else className
					for f in formatters:
						template = f.formattedTemplate(funcDef['template'], False) if funcDef['template'] else ''
						templateDollared = f.formattedTemplate(funcDef['template'], True) if funcDef['template'] else ''
						countOffset = 1 if templateDollared else 0
						paramDefs = ', '.join(['${' + str(i+1+countOffset) + ':' + f.formattedParam(param) + '}' for i, param in enumerate(funcDef['params'])])
						f.writeFunction(funcName, template, paramNames, funcName + templateDollared + '(' + paramDefs + ')' + f.FUNCTION_POSTFIX)

	for f in formatters:
		f.endSection()

for f in formatters:
	f.terminate()
