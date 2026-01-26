import os

import docx
import pdfplumber
from bs4 import BeautifulSoup



class Directory:
	def __init__(self, path):
		self.path     = path
		self.name     = os.path.basename(path)

	def __repr__(self):
		return f'<Directory: `{self.path}`>'

	# Recursively load text/markdown files into the expertise registry tree.
	# ----------------------------------------------------------------------
	def walk(self, on_subdirectory, on_file, extensions=None, recursive=True):
		for name in os.listdir(self.path):
			path = os.path.join(self.path, name)
			if os.path.isdir(path):
				subdir = Directory(path)
				on_subdirectory(subdir)
				if recursive:
					subdir.walk(on_subdirectory, on_file, extensions)
			else:
				file = File(path)
				if extensions is None or file.extension in extensions:
					on_file(file)

	# Return dict: path → last_modified_timestamp
	# ----------------------------------------------------------------------
	def list_files(self, extensions=None):
		result = {}

		for root, _, files in os.walk(self.path):
			for f in files:
				eligible = '.' in f
				extension = f.rsplit('.', 1)[-1].lower() if eligible else ''
				if extensions is not None:
					eligible = eligible and extension in extensions

				if eligible:
					path         = os.path.join(root, f)
					mtime        = os.path.getmtime(path)
					result[path] = int(mtime)

		return result


class File:
	READABLE_FILE_EXT = {'txt', 'md', 'html', 'htm', 'pdf', 'docx'}

	def __init__(self, path, encoding='utf-8'):
		self.path                   = path
		self.name                   = os.path.basename(path)
		self.prefix, self.extension = os.path.splitext(self.name)
		self.extension              = self.extension.lower().lstrip('.')
		self.encoding               = encoding

		self.readable = {
			'_'    : self._read_txt,
			'txt'  : self._read_txt,
			'md'   : self._read_txt,
			'html' : self._read_html,
			'htm'  : self._read_html,
			'pdf'  : self._read_pdf,
			'docx' : self._read_docx
		}

		self.non_writable = {
			'pdf',
			'docx',
			'doc'
		}

	def __repr__(self):
		return f'<File: `{self.path}`>'
	
	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	def _read_txt(self):
		with open(self.path, 'r', encoding=self.encoding) as f:
			return f.read()

	def _read_html(self):
		html = self._read_txt(self.path, self.encoding)
		return BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)

	def _read_pdf(self):
		out = []
		with pdfplumber.open(self.path) as pdf:
			for page in pdf.pages:
				text = page.extract_text()
				if text:
					out.append(text)
		return '\n'.join(out)

	def _read_docx(self):
		doc = docx.Document(self.path)
		return '\n'.join(p.text for p in doc.paragraphs)
	
	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Read file content
	# ----------------------------------------------------------------------
	def read(self, encoding='utf-8'):
		if File.exists(self.path):
			f = File(self.path)
			reader = f.readable.get(f.extension, f.readable['_'])
			return reader()
		return None
		
	# Write content to file
	# ----------------------------------------------------------------------
	def write(self, content, encoding='utf-8', mode='w'):
		f = File(self.path)
		if f.extension not in f.non_writable:
			with open(f.path, mode, encoding=encoding) as f:
				f.write(content)
				return True
		return False

	# Append content to file
	# ----------------------------------------------------------------------
	@classmethod
	def append(cls, path, content, encoding='utf-8'):
		return cls.write(path, content, encoding=encoding, mode='a')
	
	# Exists?
	# ----------------------------------------------------------------------
	@classmethod
	def exists(cls, path):
		return os.path.exists(path)
