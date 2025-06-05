# -----------------------------------------------------------------------------
# Core/tests/Makefile
#
#   - Builds two separate test executables:
#       * test_response_runner   (checksum + response_builder tests in test_response.c)
#       * test_drivers_runner    (INA219‐generated‐driver tests in test_generated_drivers.c)
#   - "make all" will produce both binaries.
#   - "make clean" removes all .o files and both runners.
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
# 1) RESPONSE‐BUILDER + CHECKSUM TESTS
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
# 2) INA219‐GENERATED‐DRIVER TESTS
#
#    Sources:
#      - checksum.c             (recompiled under a different object name)
#      - response_builder.c     (recompiled under a different object name)
#      - ina219.c               (low‐level HAL wrapper)
#      - ina219_config.c        (default‐config struct)
#      - driver_registry.c
#      - ina219_driver.c        (driver‐layer)
#      - hal_if_stub.c          (our I²C stub)
#      - test_generated_drivers.c  (the INA219 test harness)
#
#    We compile these into:
#      test_drivers_runner
#
#    To avoid stepping on the “_resp” objects above, we give each object here
#    a distinct name (no “_resp” suffix):
# -----------------------------------------------------------------------------
GEN_SRCS  := \
    ../Core/Src/utils/checksum.c          \
    ../Core/Src/utils/response_builder.c   \
    ../Core/Src/drivers/ina219.c           \
    ../Core/Src/config/ina219_config.c     \
    ../Core/Src/driver_registry.c          \
    ../Core/Src/drivers/ina219_driver.c    \
    hal_if_stub.c                           \
    test_generated_drivers.c

GEN_OBJS  := \
    checksum_gen.o           \
    response_builder_gen.o   \
    ina219.o                 \
    ina219_config.o          \
    driver_registry.o        \
    ina219_driver.o          \
    hal_if_stub.o            \
    test_generated_drivers.o

# Compile checksum.c → checksum_gen.o
checksum_gen.o: ../Core/Src/utils/checksum.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile response_builder.c → response_builder_gen.o
response_builder_gen.o: ../Core/Src/utils/response_builder.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile HAL‐level INA219 wrapper → ina219.o
ina219.o: ../Core/Src/drivers/ina219.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile INA219 default‐config struct → ina219_config.o
ina219_config.o: ../Core/Src/config/ina219_config.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile driver_registry.c → driver_registry.o
driver_registry.o: ../Core/Src/driver_registry.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile the INA219 driver‐layer → ina219_driver.o
ina219_driver.o: ../Core/Src/drivers/ina219_driver.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile our HAL‐IF stub → hal_if_stub.o
hal_if_stub.o: hal_if_stub.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Compile the INA219 test harness → test_generated_drivers.o
test_generated_drivers.o: test_generated_drivers.c
	$(CC) $(CFLAGS) $(INC_DIRS) -c $< -o $@

# Link ALL the INA219 objects into test_drivers_runner
test_drivers_runner: $(GEN_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $(INC_DIRS) -o $@ $(GEN_OBJS)

# -----------------------------------------------------------------------------
# “all”, “clean” and “coverage-html” targets
# -----------------------------------------------------------------------------

# By default, build both test binaries
all: test_response_runner test_drivers_runner

# Generate an HTML coverage report (requires lcov & genhtml)
coverage-html:
	@echo "==> Zeroing old coverage counters..."
	lcov --directory . --zerocounters

	@echo "==> Build, then run both test binaries..."
	# (If you haven't already built under coverage flags, run `make all` first.)
	./test_response_runner
	./test_drivers_runner

	@echo "==> Capturing coverage data into coverage.info..."
	lcov --directory . --capture --output-file coverage.info

	@echo "==> Generating HTML report under ./coverage-report/"
	rm -rf coverage-report
	genhtml coverage.info --output-directory coverage-report

	@echo ""
	@echo "=== Coverage report generated in ./coverage-report/index.html ==="

clean:
	rm -f \
	    checksum_resp.o response_builder_resp.o test_response.o test_response_runner \
	    checksum_gen.o  response_builder_gen.o  ina219.o ina219_config.o \
	    driver_registry.o ina219_driver.o hal_if_stub.o test_generated_drivers.o \
	    test_drivers_runner \
	    coverage.info \
	    *.gcda *.gcno \
	    -r coverage-report

.PHONY: all clean coverage-html
