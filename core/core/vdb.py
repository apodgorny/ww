# ======================================================================
# Vector database wrapper for FAISS + encoding helpers.
# ======================================================================

import os

os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('OMP_NUM_THREADS', '1')

import faiss
import numpy as np

from wordwield.libs.yo   import yo
from wordwield.core.sid  import Sid


class Vdb:
	def __init__(self, dim):
		self.dim         = dim # encoder.model.config.hidden_size
		self.indexes     = {}  # domain_id → FAISS index
		faiss.omp_set_num_threads(1)

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Get (or create) FAISS index for a domain
	# ----------------------------------------------------------------------
	def _get_domain_index(self, domain_id):
		if domain_id not in self.indexes:
			self.indexes[domain_id] = faiss.IndexIDMap(
				faiss.IndexFlatIP(self.dim)
			)
		return self.indexes[domain_id]

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Add vector batch with explicit IDs (Sid ints)
	# ----------------------------------------------------------------------
	def add(self, domain_id, vector_ids, vector_values):
		assert len(vector_ids) == len(vector_values)

		faiss_index = self._get_domain_index(domain_id)
		faiss_vecs  = yo.ops.Norm.sphere(vector_values).cpu().numpy().astype('float32')

		faiss_index.add_with_ids(faiss_vecs, np.array(vector_ids, dtype='int64'))

	# Remove all vectors belonging to a document (encoded in vector_id)
	# ----------------------------------------------------------------------
	def remove(self, domain_id, document_id=None):
		faiss_index = self._get_domain_index(domain_id)

		if document_id is None:
			self.vdb.indexes.pop(domain_id, None)
		else:
			id_min, id_max = Sid.get_document_id_range(document_id)
			selector = faiss.IDSelectorRange(id_min, id_max)

		faiss_index.remove_ids(selector)

	# Query vectors by vector, optionally restricted to doc_ids
	# ----------------------------------------------------------------------
	def query(self, domain_id, query_vector, k=5, document_ids=None):
		faiss_index  = self._get_domain_index(domain_id)
		query_vector = yo.ops.Norm.sphere(query_vector).reshape(1, -1)

		n = max(k * 8, 64)
		scores, ids = faiss_index.search(query_vector, n)

		allowed_docs = set(document_ids) if document_ids is not None else None
		result       = []
		seen         = set()

		for faiss_id, score in zip(ids[0], scores[0]):
			if faiss_id >= 0:
				ok = True

				if allowed_docs is not None:
					ok = Sid(faiss_id).document_id in allowed_docs

				if ok and faiss_id not in seen:
					result.append(faiss_id)
					seen.add(faiss_id)

		return result