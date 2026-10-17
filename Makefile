# NewsAlerts Makefile
# Automates building the portable standalone Windows executable

.PHONY: all build clean run check help

all: build

build:
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Task build

clean:
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Task clean

run:
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Task run

check:
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Task check

help:
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Task help
