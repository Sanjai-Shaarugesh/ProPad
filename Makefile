# Makefile for ProPad

SHELL := /bin/bash

APPDIR := /app
PREFIX := $(APPDIR)/share/propad
BINDIR := $(APPDIR)/bin
UI_DIR := ui
DATA_DIR := data
PROP_DIR := propad
SCRIPTS_DIR := scripts
PO_DIR := po
LOCALE_DIR := locale
ICONS_DIR := icons

# Default target
.PHONY: all
all: build
	@echo "ProPad build complete. Run 'make run' to start the app."

# --------------------------
# Build / Install
# --------------------------
.PHONY: build
build:
	@echo "Building ProPad..."
	mkdir -p $(PREFIX)/{ui,data,propad,scripts,po,lib,icons}
	mkdir -p $(APPDIR)/share/locale
	mkdir -p $(BINDIR)

	test -d $(UI_DIR) && cp -v $(UI_DIR)/*.ui $(PREFIX)/ui/ || true
	cp -r $(PROP_DIR)/* $(PREFIX)/propad/
	cp main.py $(PREFIX)/

	test -d $(PO_DIR) && cp -r $(PO_DIR) $(PREFIX)/ || true
	test -d $(LOCALE_DIR) && cp -r $(LOCALE_DIR) $(APPDIR)/share/locale/ || true
	test -d $(SCRIPTS_DIR) && cp -r $(SCRIPTS_DIR) $(PREFIX)/ || true
	test -d $(DATA_DIR) && cp -r $(DATA_DIR)/* $(PREFIX)/data/ || true
	test -d lib && cp -r lib/* $(PREFIX)/lib/ || true
	test -d $(ICONS_DIR) && cp -r $(ICONS_DIR)/* $(PREFIX)/icons/ || true
	find . -maxdepth 2 -name "*.css" -exec cp {} $(PREFIX)/data/ \; 2>/dev/null || true

	# Create launcher
	@echo "Creating launcher..."
	cat > $(BINDIR)/propad << 'EOF'
#!/bin/bash
export NO_AT_BRIDGE=1
export GTK_A11Y=none
export PYTHONPATH=$(PREFIX):$PYTHONPATH
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_LOADER_DRIVER_OVERRIDE=swrast
export LIBGL_DRI3_DISABLE=1
export EGL_PLATFORM=wayland
export GDK_BACKEND=wayland,x11
export GTK_USE_PORTAL=0
export WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1
export WEBKIT_FORCE_SANDBOX=0
export G_MESSAGES_DEBUG=
exec 2> >(grep -v -e "Fontconfig error" -e "Fontconfig warning" -e "Cannot load config file" -e "font-dirs.xml" -e "MESA-INTEL: warning" -e "Can't connect to a11y bus" -e "kmsro: driver missing" -e "libEGL warning" -e "egl: failed to create dri2 screen" -e "DRI2: failed to create screen" -e "Portal call failed" -e "Invalid sandbox" -e "readPIDFromPeer" -e "auxiliary process crashed" >&2)
cd $(PREFIX)
exec python3 -u main.py "$@"
EOF
	chmod +x $(BINDIR)/propad

	# Install desktop file and AppStream metadata
	install -Dm644 io.github.sanjai.ProPad.desktop /app/share/applications/io.github.sanjai.ProPad.desktop
	install -Dm644 io.github.sanjai.ProPad.metainfo.xml /app/share/metainfo/io.github.sanjai.ProPad.metainfo.xml

# --------------------------
# Run the app
# --------------------------
.PHONY: run
run: build
	@echo "Running ProPad..."
	$(BINDIR)/propad

# --------------------------
# Clean
# --------------------------
.PHONY: clean
clean:
	@echo "Cleaning build..."
	rm -rf /app/share/propad /app/share/locale /app/bin
