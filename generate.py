import pickle
import re

INPUT_FILENAME = 'unity.pkl'

OUTPUT_FILENAME = 'Unity.%s.sublime-completions'
BOO_FILENAME = OUTPUT_FILENAME % 'Boo'

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

FILE_HEADER = "{\n\t\"scope\": \"%s\",\n\n\t\"completions\":\n\t[\n"
SECTION_START_LINE = "\t\t// %s\n"
SECTION_END_LINE = "\n"
TRIGGER_LINE = "\t\t{ \"trigger\": \"%s\", \"contents\": \"%s\" },\n"
FILE_FOOTER = "\t\t{}\n\t]\n}\n"

class LangFormatter(object):
	NAME = None
	SCOPE_NAME = None
	FUNCTION_POSTFIX = None

	def formattedParam(self, param):
		return self.combineType(param['name'], self.convertTypeFromJS(param['type'])) + self.default(param['default'])

	def convertTypeFromJS(self, type_):
		return type_

	def combineType(self, name, type_):
		raise NotImplementedError

	def default(self, default):
		return ((' = ' + self.esacpe(default)) if default else '')

	def esacpe(self, s):
		return s.replace('"', '\\"')

	def convertTemplateFromJS(self, template):
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

	def convertTemplateFromJS(self, template):
		templateType = self.extractTemplateType(template)
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

	def convertTemplateFromJS(self, template):
		templateType = self.extractTemplateType(template)
		return '<%s>' % templateType

class JSFormatter(LangFormatter):
	NAME = 'JavaScript'
	SCOPE_NAME = 'source.js'
	FUNCTION_POSTFIX = ';'

	def combineType(self, name, type_):
		return '%s : %s' % (name, type_)

FORMATTERS = [BooFormatter, CSFormatter, JSFormatter]

langs = [{'name': formatter.NAME, 'formatter': formatter()} for formatter in FORMATTERS]

for lang in langs:
	lang['file'] = open(OUTPUT_FILENAME % lang['name'], 'w')
	lang['file'].write(FILE_HEADER % lang['formatter'].SCOPE_NAME)

data = pickle.load(open(INPUT_FILENAME, 'rb'))

for sectionName, sectionClasses in data.iteritems():
	logger.info(sectionName)
	for lang in langs:
		lang['file'].write(SECTION_START_LINE % sectionName)
	for className, classMembers in sectionClasses.iteritems():
		logger.info('    ' + className+ ' [class]')
		for lang in langs:
			lang['file'].write(TRIGGER_LINE % (className, className))
		for memberName, funcDefs in classMembers.iteritems():
			if funcDefs is None: # variable
				logger.info('    ' + className + '.' + memberName + ' [variable]')
				for lang in langs:
					lang['file'].write(TRIGGER_LINE % (className + '.' + memberName, className + '.' + memberName))
			else: # function
				for funcDef in funcDefs:
					paramNames = ', '.join([param['name'] for param in funcDef['params']])
					logger.info('    ' + className + '.' + memberName + ' [' + paramNames + ']')
					funcName = (className + '.' + memberName) if className != memberName else className
					for lang in langs:
						paramDefs = ', '.join(['${' + str(i+1) + ':' + lang['formatter'].formattedParam(param) + '}' for i, param in enumerate(funcDef['params'])])
						template = lang['formatter'].convertTemplateFromJS(funcDef['template']) if funcDef['template'] else ''
						lang['file'].write(TRIGGER_LINE % (funcName + template + '(' + paramNames + ')', funcName + '(' + paramDefs + ')' + lang['formatter'].FUNCTION_POSTFIX))

	for lang in langs:
		lang['file'].write(SECTION_END_LINE)

for lang in langs:
	lang['file'].write(FILE_FOOTER)
