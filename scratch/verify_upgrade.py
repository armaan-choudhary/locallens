import sys
import os
sys.path.append('backend')

# Add missing imports for config
import config
config.CHUNK_SIZE = 768
config.CHUNK_OVERLAP = 128

from ingestion.preprocessor import process_pdf
# Note: process_pdf is internal, let's mock the environment to test the internal chunker
import uuid
from typing import List, Dict

# Mocking _create_sentence_aware_chunks since it was defined inside process_pdf
# Actually, I should have defined it at module level for testability. 
# But let's verify by checking the file content again or re-running a test that calls process_pdf

