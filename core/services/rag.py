# ======================================================================
# Rag service coordinating semantic DB and vector DB.
# ======================================================================

from collections import defaultdict

import ww, yo, o


ww.schemas.SemanticDomain
ww.schemas.SemanticDocument
ww.schemas.SemanticAtom


class Rag(ww.Service):

	# To initialize vector database and hydrate it from persistent atoms.
	# ------------------------------------------------------------------
	def initialize(self):
		self.vdb = yo.models.VectorDb(yo.models.Encoder.dim)
		self._hydrate()

	# ==================================================================
	# PRIVATE METHODS
	# ==================================================================

	# Restore persistent semantic atoms into vector DB.
	# Remove all temporary domains from database.
	# ------------------------------------------------------------------
	def _hydrate(self):
		ww.Timer.start('hydration')
		# Drop all temporary domains (DB only)
		# - - - - - - - - - - - - - - - - - - - -
		for domain in o.T.SemanticDomain.get_all(temporary=True):
			domain.remove()

		# Load persistent domains into VDB
		# - - - - - - - - - - - - - - - - - - - -
		for domain in o.T.SemanticDomain.get_all(temporary=False):
			self.vdb.add_domain(domain.id)
			for document in domain.get_documents():

				vector_ids    = []
				vector_values = []

				for atom in document.get_atoms():
					vector_ids.append(atom.id)
					vector_values.append(atom.vector)

				if vector_ids:
					vectors         = yo.T.stack(vector_values)
					document_offset = min(vector_ids)

					self.vdb.add_document(
						domain.id,
						document.id,
						document_offset,
						vectors
					)
		ww.Timer.stop('hydration', report=True)

	# Split full document text into atom texts and vectors.
	# ------------------------------------------------------------------
	def _vectorize(self, text: str):
		texts   = yo.parsers.Pysbd(text)
		vectors = yo.models.Encoder.encode_sequence_batch(texts, karma=0.3, with_attentions=False)
		return texts, vectors

	# Rerank results from vdb
	# ------------------------------------------------------------------
	def _rerank(self, query, results, min_score, top_k):
		texts    = [item['text'] for item in results]
		reranked = yo.models.Reranker.score(query, texts, min_score, top_k)
		return [{**results[idx], 'score': score} for idx, score in reranked]

	# ==================================================================
	# PUBLIC METHODS
	# ==================================================================

	# Create or ensure domain exists.
	# ------------------------------------------------------------------
	def add_domain(self, key, temporary=False, description=None):
		domain = o.T.SemanticDomain(
			key         = key,
			description = description,
			temporary   = temporary
		).save()

		self.vdb.add_domain(domain.id)
		return domain

	# Remove domain and all its documents and vectors.
	# ------------------------------------------------------------------
	def remove_domain(self, id_or_key):
		domain  = o.T.SemanticDomain.load(id_or_key)

		if domain is not None:
			domain.remove()
			self.vdb.remove_domain(domain.id)
			return False

		return True

	# Create or update document and fully reindex its atoms from full text.
	# Strategy: remove and re-insert (DB), range-remove (VDB).
	# ------------------------------------------------------------------
	def add_document(self, domain_id, document_key, text, mtime, description=''):
		ww.Timer.start('vectorize')
		texts, vectors = self._vectorize(text)
		ww.Timer.stop('vectorize', report=True)
		domain         = o.T.SemanticDomain.load(domain_id)
		
		document = o.T.SemanticDocument(
			key         = document_key,
			domain      = domain,
			mtime       = mtime,
			description = description
		).save()

		ww.Timer.start('add_atoms')
		o.Db.tx_begin()
		vector_ids      = document.add_atoms(texts, vectors)
		o.Db.tx_end()
		ww.Timer.stop('add_atoms', report=True)
		document_offset = min(vector_ids)

		self.vdb.add_document(
			domain_id,
			document.id,
			document_offset,
			vectors
		)
		return document

	# Remove document and all its atoms (DB + VDB)
	# ------------------------------------------------------------------
	def remove_document(self, domain_id, document_id):
		document = o.T.SemanticDocument.load(document_id)

		if document is not None:
			self.vdb.remove_document(domain_id, document_id)
			document.remove()
			return True

		return False

	# List documents in domain
	# ------------------------------------------------------------------
	def get_documents(self, domain_id):
		domain = o.T.SemanticDomain.load(domain_id)
		return domain.get_documents() if domain is not None else []

	# Search
	# ------------------------------------------------------------------
	def search(self, domain_id_or_key, query, top_k):
		ww.Timer.start('search')
		domain  = o.T.SemanticDomain.load(domain_id_or_key)
		self.print(f'Searching domain `{domain.key}`')
		results = []

		if domain is not None:
			query_vector = yo.models.Encoder.encode(query)
			doc_scores   = self.vdb.query(query_vector, domain.id, k = top_k)

			for document_id, atoms in doc_scores.items():
				document = o.T.SemanticDocument.load(document_id)

				for atom_id, score in atoms.items():
					atom = o.T.SemanticAtom.load(atom_id)

					results.append({
						'domain'   : domain,
						'document' : document,
						'atom'     : atom,
						'text'     : atom.text,
						'score'    : score,
					})
					
			min_score = 0.5
			results = self._rerank(query, results, min_score, top_k)

			d = defaultdict(list)
			for result in results:
				item = (result['atom'].id, result['score'], result['text'])
				d[result['document'].key].append(item)

			for key in d:
				d[key].sort(key=lambda x: x[0])
			ww.Timer.stop('search', report=True)

		return d



	