"""
Parses the IOP tcl code to generate web documentation

Run with option --help for usage info.
"""

## @package tops.sdss3.design.iop
# Parses the IOP tcl code to generate web documentation
#
# @author David Kirkby, dkirkby@uci.edu
# @date Created 1-Oct-2008
#
# This project is hosted at http://tops.googlecode.com/

class EndOfTokens(Exception):
	pass
	
class FatalParseError(Exception):
	pass

import ply.lex as lex

class LexicalAnalyzer(object):
	"""
	Splits a tcl file into parsing tokens based on a lexical analysis
	
	Uses the PLY lexer to do the hard work.
	"""
	# list the single-character literal tokens we care about
	literals = '{}#$"\[\];'

	# list the non-literal token types defined below
	tokens = ('WS','EOL','WORD')

	# inline whitespace
	t_WS = r'[ \t]+'

	# collapse multiple newlines separated by whitespace into a single EOL token
	t_EOL = r'\n[ \t\n]*'

	# Define a TCL word as a sequence of non-whitespace characters excluding the literals above
	# unless they are escaped.
	t_WORD = r'([^%s\\ \t\n]|(\\.))+' % (literals)
	#t_WORD = r'([^%s \t\n]|(\\[%s]))+' % (literals,literals)

	def t_error(self,t):
		raise FatalParseError("Illegal character on line %d: '%s'" % (1+t.lineno,t.value))

	def __init__(self):
		self.lexer = lex.lex(object=self)

from tops.core.utility.html import *

class File(object):
	"""
	Prepares a tcl file for parsing
	
	A debug level of 0 is silent unless there is a fatal error. Level 2
	prints the line numbers where each parsing unit begins and ends.
	Level 3 also prints each token.
	"""
	def __init__(self,name,lexer,debug=0):
		self.data = ''
		self.offsets = [ ]
		self.escapes = [ ]
		offset = 0
		for line in open(name):
			self.offsets.append(offset)
			offset += len(line)
			if line[-2:] == '\\\n':
				if debug > 1:
					print 'removing escaped newline at end of line',len(self.offsets)
				# replace an escaped newline with two spaces to preserve offsets
				self.data += line[:-2]
				self.data += '  '
				self.escapes.append(offset-2)
			else:
				self.data += line
		self.nlines = len(self.offsets)
		self.lexer = lexer
		self.debug = debug
		self.last_line = 0
		self.script = None

	def lineno(self,offset=None):
		"""
		Returns the line number in the input file for the given offset
		
		Because of escaped-newline processing, line numbers in the
		parsed stream can be different from those returned here. If no
		offset is provided, uses the offset where the next token will
		start.
		"""
		if not offset:
			offset = self.lexer.lexpos
		# continue from the last line unless we have gone backwards
		if offset >= self.offsets[self.last_line]:
			line = self.last_line
		else:
			line = 0
		# scan forwards to find which line the offset is on
		while line < self.nlines and offset >= self.offsets[line]:
			line += 1
		self.last_line = line - 1
		return line
		
	def next_token(self):
		"""
		Returns the next token from the file
		
		Raises an EndOfTokens exception if there are no more tokens
		available. The returned token will have a lineno and value set
		as if there had been no escaped-newline processing of the file.
		"""
		token = self.lexer.token()
		if not token:
			raise EndOfTokens
		# store this token's line number based on its file offset
		token.lineno = self.lineno(token.lexpos)
		# undo any escaped-newline substitution applied to this token's value
		start = token.lexpos
		end = start + len(token.value)
		for offset in self.escapes:
			if offset < start or offset >= end:
				continue
			pos = offset - start
			token.value = token.value[:pos] + '\\\n' + token.value[pos+2:]
			if self.debug > 1:
				print 'restored escaped newline at end of line',token.lineno
			break
		# print out each token if we are being verbose
		if self.debug > 2:
			print 'shift',token
		return token
		
	def parse(self):
		"""
		Parses this file and returns a Script object
		
		Raises a FatalParseError exception if there is a problem.
		"""
		self.lexer.input(self.data)
		try:
			self.script = Script(self,self.debug)
			return self.script
		except FatalParseError,e:
			print 'ERROR:',e
			
	def export(self,filename,title,stylesheet='tclcode.css'):
		if not self.script:
			print 'file has not been successfully parsed yet, nothing to export'
			return
		doc = HTMLDocument(
			Head(title=title,css=stylesheet),
			Body(
				H1(title),
				Div(id='content')
			)
		)
		self.script.export(doc['content'])
		f = open(filename,'w')
		print >> f,doc
		f.close()

class Parser(object):
	"""
	Provides functionality needed by all language element parsers
	"""	
	prefix = ''
	suffix = ''

	def __init__(self,tokenizer,debug,info=''):
		self.tokenizer = tokenizer
		self.debug = debug
		self.tokens = [ ]
		self.stream = [ ]
		self.name = self.__class__.__name__
		if debug > 1:
			print 'line %4d: %s begin %s' % (tokenizer.lineno(),self.name,info)
		self.parse(debug)
		if debug > 1:
			print 'line %4d: %s end   %s' % (tokenizer.lineno(),self.name,info)

	def next(self,end_is_fatal=True):
		"""
		Returns the next token
		
		Raises a fatal error if end_is_fatal is True (the default) and
		there are no more tokens available. Stores the lexical tokens
		read by this instance in the stream array.
		"""
		try:
			token = self.tokenizer.next_token()
			self.stream.append(token)
			return token
		except EndOfTokens:
			if end_is_fatal:
				raise FatalParseError('unexpected EOF in %s' % self.name)
			else:
				raise

	def __repr__(self):
		return '%s%s' % (self.name,str(self.tokens))
		
	def reconstruct(self):
		"""
		Reconstructs the string that was parsed to create this instance
		
		Sublcasses should provide appropriate values for the prefix and
		suffix class attributes to define their wrapper tokens.
		"""
		data = self.prefix
		for token in self.tokens:
			if isinstance(token,Parser):
				data += token.reconstruct()
			else:
				data += token.value
		data += self.suffix
		return data
		
	def export(self,container):
		"""
		Fills the DOM container with an HTML description of this instance
		"""
		content = Span(className=self.name)
		if self.prefix:
			content.append(self.prefix)
		for token in self.tokens:
			if isinstance(token,Parser):
				token.export(content)
			elif isinstance(token,lex.LexToken):
				# is this literal tagged?
				if hasattr(token,'tag'):
					content.append(Span(token.value,id=token.tag,className='tagged'))
				else:
					content.append(token.value)
			else:
				print 'export: ignoring illegal token "%s"' % token
		if self.suffix:
			content.append(self.suffix)
		container.append(content)
		
	def append(self,type_or_value,*type_args):
		"""
		Appends a new token of the specified type or value
		"""
		if isinstance(type_or_value,type):
			self.tokens.append(type_or_value(self.tokenizer,self.debug,*type_args))
		elif isinstance(type_or_value,lex.LexToken):
			self.tokens.append(type_or_value)
		else:
			raise FatalParseError('append: unrecognized token type: %r' % type_or_args)
			
	def embed(self):
		"""
		Re-parses this object as an embedded self-contained script
		"""
		if self.debug:
			print 're-parsing %s as an embedded script' % self.name
		try:
			embedded = EmbeddedScript(self.tokenizer,self.debug,parent=self)
			self.tokens[:] = [embedded]
		except FatalParseError,e:
			if self.debug:
				print 're-parse failed:' % e

class Script(Parser):
	"""
	Represents a tcl script consisting of a sequence of Commands
	"""
	def parse(self,debug):
		try:
			while True:
				self.append(Command)
		except EndOfTokens:
			pass
			
class EmbeddedScript(Script):
	"""
	Represents a complete script embedded within a parse object
	
	The embedded script is built by replaying the lexical tokens of
	the specified parent parse object.
	"""
	def __init__(self,tokenizer,debug,parent):
		# we use our parent's lexical stream as our token source
		self.source = parent.stream[:]
		if parent.suffix:
			assert(self.source[-1].value == parent.suffix)
			del self.source[-1]
		self.index = 0
		# we take over the tokenizer's job ourself
		Script.__init__(self,tokenizer=self,debug=debug)
		
	def lineno(self):
		"""
		Returns the line number corresponding to the next token
		"""
		try:
			return self.source[self.index].lineno
		except IndexError:
			try:
				return self.source[-1].lineno
			except IndexError:
				return -1
			
	def next_token(self):
		"""
		Returns the next token or raises EndOfTokens
		"""
		try:
			token = self.source[self.index]
			self.index += 1
			if self.debug > 2:
				print 'shift',token
			return token
		except IndexError:
			raise EndOfTokens()
	
class Command(Parser):
	"""
	Represents a tcl command
	
	A commmand is either a Comment or a sequence of words, each
	represented by a string, Variable, Substitution, Quoted, or Group.
	The whitespace between words is preserved so that the original file
	can be exactly reconstructed after parsing.
	"""
	def parse(self,debug):
		while True:
			try:
				token = self.next(end_is_fatal=False)
			except EndOfTokens:
				if len(self.tokens) > 0:
					if debug > 1:
						print 'non-empty final line is missing \\n'
					break
				else:
					raise
			if token.type in ('EOL',';'):
				self.append(token)
				break
			elif token.type == '#':
				# only white space can precede a valid comment
				is_comment = True
				for tok in self.tokens:
					if not isinstance(tok,lex.LexToken):
						is_comment = False
						break
					if not tok.type in ('WS','EOL'):
						is_comment = False
						break
				if is_comment:
					self.append(Comment)
					break
				else:
					if debug:
						print 'found non-comment # in command on line %d' % token.lineno
					self.append(token)
			elif token.type == '$':
				self.append(Variable)
			elif token.type == '[':
				self.append(Substitution)
			elif token.type == '"':
				self.append(Quoted)
			elif token.type == '{':
				self.append(Group)
			elif token.type == '}':
				raise FatalParseError('unexpected } on line %d during Command' % token.lineno)
			elif token.type == ']':
				raise FatalParseError('unexpected ] on line %d during Command' % token.lineno)
			else:
				self.append(token)
		# extract the words of this command, if any, ignoring whitespace and comments
		words = [ ]
		for tok in self.tokens:
			if isinstance(tok,lex.LexToken) and tok.type in ('WS','EOL'):
				continue
			if isinstance(tok,Comment):
				continue
			words.append(tok)
		if len(words) == 0:
			return
		# do we have a literal base word?
		if not isinstance(words[0],lex.LexToken) or words[0].type != 'WORD':
			return
		baseword = words[0].value
		# should we do any further processing of this command?
		if baseword == 'proc':
			# Process a tcl 'proc' command: http://www.tcl.tk/man/tcl8.4/TclCmd/proc.htm
			# a proc command should always have 4 words
			if len(words) != 4:
				if debug:
					print ('ignoring "proc" with %d words (expected 4) on line %d'
						% (len(words),words[0].lineno))
				return
			# expand the procedure body if it is a Group
			#if isinstance(words[3],Group):
			#	words[3].embed()
			# do we have a literal proc name?
			if not isinstance(words[1],lex.LexToken) or words[1].type != 'WORD':
				if debug:
					print 'ignoring "proc" with computed name on line %d' % words[0].lineno
				return
			# record this procedure definition in the global dictionary
			proc_name = words[1].value
			if proc_name in tclproc:
				tclproc[proc_name].append(filetitle)
				tag = "%s_%d" % (proc_name,len(tclproc[proc_name]))
			else:
				tclproc[proc_name] = [ filetitle ]
				tag = proc_name
			# tag the procedure name for our HTML markup
			words[1].tag = tag

class Comment(Parser):
	"""
	Represents a tcl comment
	
	Comments begin with a '#' symbol where the start of a new command is
	expected, and end with the first un-escaped newline.
	"""
	prefix = '#'
	
	def parse(self,debug):
		while True:
			token = self.next()
			self.append(token)
			if token.type == 'EOL':
				break

class Quoted(Parser):
	"""
	Represents a tcl quoted word delimeted by double quotes
	
	The word contents will be parsed to detect any embedded command or
	variable substitutions, or embedded groups.
	"""	
	prefix = '"'
	suffix = '"'

	def parse(self,debug):
		while True:
			token = self.next()
			if token.type == '$':
				self.append(Variable)
			elif token.type == '[':
				self.append(Substitution)
			elif token.type == '{':
				self.append(Group)
			elif token.type == '}':
				raise FatalParseError('unexpected } on line %d during Quoted' % token.lineno)
			elif token.type == ']':
				raise FatalParseError('unexpected ] on line %d during Quoted' % token.lineno)
			elif token.type == '"':
				break
			else:
				self.append(token)

class Group(Parser):
	"""
	Represents a tcl group delimited by { }
	
	Groups are considered opaque words in tcl so no command or variable
	substitutions will be detected within a group. However, any embedded
	'{' must be balanced by a closing '}' within the group. This is
	accomplished here by creating a nested Group for each '{' even
	though this is not semantically meaningful (since the top-level
	group is an entire tcl word) and is applied to non-group constructs
	like ${variable}.
	"""
	prefix = '{'
	suffix = '}'
	
	def __init__(self,tokenizer,debug,depth=1):
		self.depth = depth
		info = '-'*depth + ('> %2d' % depth)
		Parser.__init__(self,tokenizer,debug,info)
	
	def parse(self,debug):
		while True:
			token = self.next()
			if token.type == '{':
				self.append(Group,self.depth+1)
			elif token.type == '}':
				break
			else:
				self.append(token)

class Substitution(Parser):
	"""
	Represents a tcl command substitution delimited by [ ]
	"""
	prefix = '['
	suffix = ']'
	
	def parse(self,debug):
		while True:
			token = self.next()
			if token.type == ']':
				break
			elif token.type == '[':
				self.append(Substitution)
			elif token.type == '{':
				self.append(Group)
			elif token.type in ('EOL','}'):
				raise FatalParseError('unexpected Substitution token %s' % token)
			else:
				self.append(token)
		# now that we have captured the whole substitution text, try to
		# re-parse it as an embedded script
		self.embed()

class Variable(Parser):
	"""
	Represents a tcl variable substition starting with $
	
	Completely captures the $name and ${name} forms, but will generally
	only capture the beginning of $name(index) - up to the first white
	space in 'index'. The main purpose of this parser is to distinguish
	between '{' used to start a group and '${' used to start a variable
	substitution.
	"""
	prefix = '$'
	
	def parse(self,debug):
		while True:
			token = self.next()
			if token.type == '{':
				if len(self.tokens) == 0:
					self.append(token)
					while True:
						token = self.next()
						self.append(token)
						if token.type == '}':
							break
					break
				else:
					raise FatalParseError('unexpected { in Variable on line %d' % token.lineno)
			elif token.type == 'WORD':
				# will match $name and part or all of $name(index)
				self.append(token)
				break
			else:
				raise FatalParseError('unexpected token %s in Variable' % token)
			

import sys,os,os.path

def process_file(source,opath,title,debug=0):
	"""
	Processes source and generates a corresponding html file in opath
	
	source should be the name of an existing tcl file. opath should
	either be None (in which case no output will be generated) or else
	the name of path where the generated output will go. The opath
	directory will be created if necessary.
	"""
	if not os.path.isfile(source):
		raise FatalParseError("not a valid source file: %s" % source)
	if opath and not os.path.exists(opath):
		os.makedirs(opath)
	if opath and not os.path.isdir(opath):
		raise FatalParseError("not a valid output directory: %s" % opath)
	f = File(source,lexer,debug=opts.debug)
	if debug:
		print 'parsing %s (%d lines)' % (source,f.nlines)
	script = f.parse()
	if script:
		if debug > 3:
			print script
		if opath:
			(ofile,ext) = os.path.splitext(os.path.basename(source))
			ofile = os.path.join(opath,ofile+'.html')
			if debug:
				print 'generating',ofile
			f.export(ofile,title)

if __name__ == '__main__':
	
	from optparse import OptionParser

	# parse command-line options
	options = OptionParser(usage = 'usage: %prog [options] source')
	options.add_option("-d","--debug",type="int",metavar="INT",
		help="debug printout level (0=none, default is %default)")
	options.add_option("-o","--output",metavar="PATH",
		help="output path (created if necessary, omit for no output)")
	options.add_option("-R","--recursive",action="store_true",
		help="recursively visit all source tcl files (%default by default)")
	options.set_defaults(debug=0,recursive=False)
	(opts,args) = options.parse_args()

	# validate command-line options
	if opts.debug:
		print 'debug level is %d' % opts.debug
	if len(args) != 1:
		options.print_help()
		sys.exit(-1)
	source = args[0]
	if not os.path.exists(source):
		print 'no such source: %s' % source
		sys.exit(-2)

	# one-time initialization of lexical analyzer
	lexer = LexicalAnalyzer().lexer
	
	# Initialize a dictionary of tcl procedures. Keys are procedure names
	# with an array of filenames as the corresponding value. Note that a tcl
	# procedure of the same name can be defined more than once, even in the
	# same file.
	tclproc = { }
	
	# do we just have a single file to parse?
	if os.path.isfile(source):
		filetitle = os.path.basename(source)
		process_file(source,opts.output,filetitle,opts.debug)
		sys.exit(0)
		
	# walk through the source tree
	for (root,dirs,files) in os.walk(source):
		if not opts.recursive:
			del dirs[:]
		# calculate the output path
		if opts.output:
			ipath = root
			opathsegs = [ ]
			while not os.path.samefile(ipath,source):
				(ipath,seg) = os.path.split(ipath)
				opathsegs.append(seg)
			opathsegs.reverse()
			opath = opts.output
			title = ''
			for seg in opathsegs:
				title = os.path.join(title,seg)
				opath = os.path.join(opath,seg)
		else:
			opath = None
			title = None
		for filename in files:
			# process any tcl files in this directory
			(base,ext) = os.path.splitext(filename)
			if ext != '.tcl':
				continue
			filetitle = os.path.join(title,filename)
			filename = os.path.join(root,filename)
			process_file(filename,opath,filetitle,opts.debug)
