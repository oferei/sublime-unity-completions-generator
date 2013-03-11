import pickle

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
		return self.combineType(param['name'], param['type']) + self.default(param['default'])

	def combineType(self, name, type_):
		raise NotImplementedError

	def default(self, default):
		return ((' = ' + self.esacpe(default)) if default else '')

	def esacpe(self, s):
		return s.replace('"', '\\"')

class BooFormatter(LangFormatter):
	NAME = 'Boo'
	SCOPE_NAME = 'source.boo'
	FUNCTION_POSTFIX = ''
	def combineType(self, name, type_):
		return '%s as %s' % (name, type_)

class CSFormatter(LangFormatter):
	NAME = 'CS'
	SCOPE_NAME = 'source.cs'
	FUNCTION_POSTFIX = ';'
	def combineType(self, name, type_):
		return '%s %s' % (type_, name)

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

# booFile = open(BOO_FILENAME, 'w')
# booFile.write(FILE_HEADER % 'source.boo')

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
					# ${1:index as int}
					# paramDefs = ', '.join(['${' + str(i+1) + ':' + (param['name'] + ' as ' + param['type'] + ((' = ' + param['default'].replace('"', '\\"')) if param['default'] else '') + '}') for i, param in enumerate(funcDef['params'])])
					logger.info('    ' + className + '.' + memberName + ' [' + paramNames + ']')
					funcName = (className + '.' + memberName) if className != memberName else className
					# booFile.write(TRIGGER_LINE % (funcName + '(' + paramNames + ')', funcName + '(' + paramDefs + ')'))
					for lang in langs:
						paramDefs = ', '.join(['${' + str(i+1) + ':' + lang['formatter'].formattedParam(param) + '}' for i, param in enumerate(funcDef['params'])])
						lang['file'].write(TRIGGER_LINE % (funcName + '(' + paramNames + ')', funcName + '(' + paramDefs + ')' + lang['formatter'].FUNCTION_POSTFIX))


	for lang in langs:
		lang['file'].write(SECTION_END_LINE)

for lang in langs:
	lang['file'].write(FILE_FOOTER)
