# ======================================================================
# Configuration
# ======================================================================
APP_NAME := "propad"
APP_ID := "io.github.sanjai.ProPad"
LOCALE_DIR := "locale"
PO_DIR := "po"
LANGUAGES := "en es fr de it pt ru ar hi bn gu ta zh_CN ja ko th"


# ======================================================================
# Default target
# ======================================================================
default:
    @just --list

# ======================================================================
# UI BUILD
# ======================================================================
build-ui:
    blueprint-compiler compile lib/window.blp > ui/window.ui
    blueprint-compiler compile lib/sidebar.blp > ui/sidebar.ui
    blueprint-compiler compile lib/webview.blp > ui/webview.ui
    blueprint-compiler compile lib/export_dialog.blp > ui/export_dialog.ui
    blueprint-compiler compile lib/search_replace.blp > ui/search_replace.ui
    blueprint-compiler compile lib/formatting_toolbar.blp > ui/formatting_toolbar.ui
    blueprint-compiler compile lib/file_manager.blp > ui/file_manager.ui
    blueprint-compiler compile lib/shortcuts_window.blp > ui/shortcuts_window.ui

# ======================================================================
# DEVELOPMENT
# ======================================================================
format: build-ui
    uv run ruff format .

check-format: format
    uv run ruff format --check

run: check-format
    uv run main.py

# Run with a specific language
run-lang LANG: check-format fix-translations compile-translations
    LANGUAGE={{LANG}} uv run main.py

# ======================================================================
# TRANSLATION
# ======================================================================
extract-strings:
    mkdir -p {{PO_DIR}}
    xgettext --keyword=_ --keyword=N_ --keyword=C_:1c,2 \
        --language=Python --from-code=UTF-8 \
        --output={{PO_DIR}}/{{APP_NAME}}.pot \
        --no-wrap \
        --sort-output \
        main.py src/*.py
    @echo "✓ Extracted strings to {{PO_DIR}}/{{APP_NAME}}.pot"

fix-translations:
    #!/usr/bin/env bash
    for po in {{PO_DIR}}/*.po; do
        echo "Cleaning $po..."
        if msguniq "$po" -o "$po.tmp" 2>/dev/null; then
            mv "$po.tmp" "$po"
            echo "  ✓ Success"
        else
            echo "  ✗ Failed - file may be corrupted, skipping"
            rm -f "$po.tmp"
        fi
    done

# Repair corrupted .po files by recreating from template
repair-translations:
    #!/usr/bin/env bash
    if [ ! -f "{{PO_DIR}}/{{APP_NAME}}.pot" ]; then
        echo "Error: Template file {{PO_DIR}}/{{APP_NAME}}.pot not found"
        echo "Run 'just extract-strings' first"
        exit 1
    fi
    for lang in {{LANGUAGES}}; do
        po_file="{{PO_DIR}}/$lang.po"
        if [ -f "$po_file" ]; then
            echo "Checking $po_file..."
            if ! msgfmt -c "$po_file" 2>/dev/null; then
                echo "  Repairing $lang..."
                msgmerge --backup=none -U "$po_file" "{{PO_DIR}}/{{APP_NAME}}.pot" 2>/dev/null || \
                    msginit --no-translator -l "$lang" -i "{{PO_DIR}}/{{APP_NAME}}.pot" -o "$po_file"
                echo "  ✓ Repaired"
            else
                echo "  ✓ OK"
            fi
        fi
    done

# Generate .po files for all configured languages
generate-all-po:
    #!/usr/bin/env bash
    if [ ! -f "{{PO_DIR}}/{{APP_NAME}}.pot" ]; then
        echo "Error: Template file {{PO_DIR}}/{{APP_NAME}}.pot not found"
        echo "Run 'just extract-strings' first"
        exit 1
    fi
    echo "Cleaning .pot file..."
    msguniq "{{PO_DIR}}/{{APP_NAME}}.pot" -o "{{PO_DIR}}/{{APP_NAME}}.pot.tmp"
    mv "{{PO_DIR}}/{{APP_NAME}}.pot.tmp" "{{PO_DIR}}/{{APP_NAME}}.pot"
    for lang in {{LANGUAGES}}; do
        po_file="{{PO_DIR}}/$lang.po"
        if [ ! -f "$po_file" ]; then
            echo "Creating $po_file..."
            msginit --no-translator -l "$lang" -i "{{PO_DIR}}/{{APP_NAME}}.pot" -o "$po_file"
        else
            echo "Updating $po_file..."
            msgmerge --backup=none -U "$po_file" "{{PO_DIR}}/{{APP_NAME}}.pot"
        fi
    done
    echo "✓ All .po files generated/updated"

# Clean workflow: extract, generate, and compile translations
rebuild-translations:
    just extract-strings
    just generate-all-po
    just compile-translations
    echo ""
    echo "✓ Translation workflow complete!"

# Recreate corrupted .po files from scratch
recreate-corrupted:
    #!/usr/bin/env bash
    if [ ! -f "{{PO_DIR}}/{{APP_NAME}}.pot" ]; then
        echo "Error: Template file not found. Run 'just extract-strings' first"
        exit 1
    fi
    corrupted_langs="bn en_GB gu kn ml mr pa te"
    for lang in $corrupted_langs; do
        po_file="{{PO_DIR}}/$lang.po"
        echo "Recreating $po_file..."
        rm -f "$po_file"
        msginit --no-translator -l "$lang" -i "{{PO_DIR}}/{{APP_NAME}}.pot" -o "$po_file" 2>/dev/null || \
            msginit --no-translator --locale="$lang" -i "{{PO_DIR}}/{{APP_NAME}}.pot" -o "$po_file"
        if [ -f "$po_file" ]; then
            echo "  ✓ Created"
        else
            echo "  ✗ Failed"
        fi
    done
    echo ""
    echo "✓ Recreated corrupted .po files"

compile-translations: fix-translations
    #!/usr/bin/env bash
    mkdir -p {{LOCALE_DIR}}
    failed=0
    for lang in {{LANGUAGES}}; do
        po_file="{{PO_DIR}}/$lang.po"
        if [ -f "$po_file" ]; then
            mkdir -p "{{LOCALE_DIR}}/$lang/LC_MESSAGES"
            if msgfmt "$po_file" -o "{{LOCALE_DIR}}/$lang/LC_MESSAGES/{{APP_NAME}}.mo" 2>/dev/null; then
                echo "✓ Compiled $lang"
            else
                echo "✗ Failed to compile $lang (file may be corrupted)"
                failed=$((failed + 1))
            fi
        fi
    done
    if [ $failed -gt 0 ]; then
        echo ""
        echo "Warning: $failed translation(s) failed to compile"
        echo "Run 'just repair-translations' to attempt repair"
    fi

# ======================================================================
# FLATPAK
# ======================================================================
flatpak-setup:
    flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

flatpak-deps: flatpak-setup
    flatpak install --user -y flathub org.gnome.Platform//48 org.gnome.Sdk//48 || true

flatpak-build: flatpak-deps build-ui compile-translations
    flatpak-builder --force-clean --repo=repo build-dir {{APP_ID}}.yaml

flatpak-run: flatpak-build
    flatpak-builder --run build-dir {{APP_ID}}.yaml propad

flatpak-run-lang LANG: flatpak-build
    flatpak-builder --run build-dir {{APP_ID}}.yaml sh -c "LANGUAGE={{LANG}} propad"

flatpak-install: flatpak-build
    flatpak-builder --user --install --force-clean build-dir {{APP_ID}}.yaml

flatpak-uninstall:
    flatpak uninstall --user -y {{APP_ID}} || true

flatpak-clean:
    rm -rf build-dir .flatpak-builder repo

flatpak-bundle: flatpak-build
    flatpak build-bundle repo ProPad.flatpak {{APP_ID}}

# ======================================================================
# SYSTEM INSTALL
# ======================================================================
build: build-ui compile-translations

install: build
    sudo mkdir -p /usr/local/share/propad
    sudo cp -r ui assets data src main.py /usr/local/share/propad/
    sudo cp -r locale/* /usr/share/locale/ || true
    sudo chmod +x /usr/local/share/propad/main.py
    sudo ln -sf /usr/local/share/propad/main.py /usr/local/bin/propad

uninstall:
    sudo rm -rf /usr/local/share/propad
    sudo rm -f /usr/local/bin/propad

# ======================================================================
# TEST + LINT
# ======================================================================
test:
    uv run pytest tests/ -v

lint:
    uv run ruff check .

lint-fix:
    uv run ruff check --fix .

# ======================================================================
# CLEAN
# ======================================================================
clean:
    rm -rf {{LOCALE_DIR}} build-dir repo .flatpak-builder ProPad.flatpak
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -name "*.pyc" -delete