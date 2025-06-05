# -----------------------------------------------------------------------------
# Core/tests/Makefile
#
#   - Builds a single test executable:
#       * test_response_runner   (checksum + response_builder tests in test_response.c)
#   - "make all" will produce the test_response_runner binary.
#   - "make clean" removes all .o files, the test binary, and coverage artifacts.
#   - "make coverage-html" will generate an HTML coverage report under coverage-report/
# -----------------------------------------------------------------------------

CC       := gcc
CFLAGS   := -std=c99 -Wall -Wextra -DTEST -fprofile-arcs -ftest-coverage
LDFLAGS  := -fprofile-arcs -ftest-coverage

# -----------------------------------------------------------------------------
# Include stub headers first, then the real Core/Inc paths:
# -----------------------------------------------------------------------------
INC_DIRS := \
    -Istub_includes \
    -I../Core/Inc \
    -I../Core/Inc/utils \
    -I../Core/Inc/drivers

# -----------------------------------------------------------------------------
# RESPONSE‐BUILDER + CHECKSUM TESTS
#
#   Sources:
#     - checksum.c
#     - response_builder.c
#     - test_response.c       (the “response+checksum” test harness)
#
#   We compile these into:
#     test_response_runner
#
#   To avoid object‐file name conflicts with other tests, we append “_resp”
#   to each object file used here.
# -----------------------------------------------------------------------------
RESP_SRCS := \
    ../Core/Src/utils/checksum.c        \
    ../Core/Src/utils/response_builder.c \
    test_response.c

RESP_OBJS := \
    checksum_resp.o        \
    response_builder_resp.o \
    test_response.o

# Compile checksum.c → checksum_resp.o
checksum_resp.o: ../Core/Src/utils/checksum.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile response_builder.c → response_builder_resp.o
response_builder_resp.o: ../Core/Src/utils/response_builder.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile test_response.c → test_response.o
test_response.o: test_response.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Link the “response” test into test_response_runner
test_response_runner: $(RESP_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $(INC_DIRS) -o $@ $(RESP_OBJS)

# -----------------------------------------------------------------------------
# “all”, “clean” and “coverage-html” targets
# -----------------------------------------------------------------------------

# By default, build the response test binary
all: test_response_runner

# Generate an HTML coverage report (requires lcov & genhtml)
coverage-html:
	@echo "==> Zeroing old coverage counters..."
	lcov --directory . --zerocounters

	@echo "==> Build (if needed), then run the response test binary..."
	# (If you haven't already built under coverage flags, run `make all` first.)
	./test_response_runner

	@echo "==> Capturing coverage data into coverage.info..."
	lcov --directory . --capture --output-file coverage.info

	@echo "==> Generating HTML report under ./coverage-report/"
	rm -rf coverage-report
	genhtml coverage.info --output-directory coverage-report

	@echo ""
	@echo "=== Coverage report generated in ./coverage-report/index.html ==="

clean:
	# Remove coverage data files
	find . -name '*.gcda' -delete
	find . -name '*.gcno' -delete

	# Remove object files, test binary, coverage info, and report folder
	rm -f \
	    checksum_resp.o response_builder_resp.o test_response.o \
	    test_response_runner \
	    coverage.info

	rm -rf coverage-report

.PHONY: all clean coverage-html
