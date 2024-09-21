"""Benchmarks for PavedPath."""

import logging
import time
from pathlib import Path

from src.paved_path import PavedPath

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
ITERATIONS = 100_000

# Make a 1MB test file
test_path = PavedPath(__file__).parent / "test-file"
test_data = bytes([i % 256 for i in range(1024 * 1024)])
test_path.write_bytes(test_data)

# The original read_bytes function
pathlib_test_path = Path(test_path)
start_time = time.time()
for _ in range(ITERATIONS):
    pathlib_test_path.read_bytes()
end_time = time.time()
execution_time = end_time - start_time
logging.info("read_bytes: %.6f seconds", execution_time)

# read_bytes_cached with reload=True
start_time = time.time()
for _ in range(ITERATIONS):
    test_path.read_bytes(reload=True)
end_time = time.time()
execution_time = end_time - start_time
logging.info("cached reload: %.6f seconds", execution_time)

# read_bytes_cached with check_file=True
start_time = time.time()
for _ in range(ITERATIONS):
    test_path.read_bytes(check_file=True)
end_time = time.time()
execution_time = end_time - start_time
logging.info("check_file: %.6f seconds", execution_time)

# read_bytes_cached with no extra arguments
start_time = time.time()
for _ in range(ITERATIONS):
    test_path.read_bytes()
end_time = time.time()
execution_time = end_time - start_time
logging.info("cached: %.6f seconds", execution_time)

# Clean up
test_path.delete_file()
