"""Benchmarks for PavedPath."""

import logging
import time

from src.paved_path import PavedPath

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
ITERATIONS = 100_000

# Make a 1MB test file
test_path = PavedPath("test-file")
test_data = bytes([i % 256 for i in range(1024 * 1024)])
test_path.write_bytes(test_data)

# The original read_bytes function
start_time = time.time()
for _ in range(ITERATIONS):
    test_path.read_bytes()
end_time = time.time()
execution_time = end_time - start_time
logging.info("read_bytes:        %.6f seconds", execution_time)

# read_bytes_cached with reload=True
test_path = PavedPath("test-file")
start_time = time.time()
for _ in range(ITERATIONS):
    test_path.read_bytes_cached(reload=True)
end_time = time.time()
execution_time = end_time - start_time
logging.info("cached reload:     %.6f seconds", execution_time)

# read_bytes_cached with check_file=True
start_time = time.time()
for _ in range(ITERATIONS):
    test_path.read_bytes_cached(check_file=True)
end_time = time.time()
execution_time = end_time - start_time
logging.info("cached check_file: %.6f seconds", execution_time)

# read_bytes_cached with no extra arguments
start_time = time.time()
for _ in range(ITERATIONS):
    test_path.read_bytes_cached()
end_time = time.time()
execution_time = end_time - start_time
logging.info("read_bytes_cached: %.6f seconds", execution_time)

# Clean up
test_path.delete_file()
