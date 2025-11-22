# Development commands
build-ui:
    blueprint-compiler compile lib/window.blp > ui/window.ui
    blueprint-compiler compile lib/sidebar.blp > ui/sidebar.ui
    blueprint-compiler compile lib/webview.blp > ui/webview.ui
    blueprint-compiler compile lib/export_dialog.blp > ui/export_dialog.ui
    blueprint-compiler compile lib/search_replace.blp > ui/search_replace.ui
    blueprint-compiler compile lib/formatting_toolbar.blp > ui/formatting_toolbar.ui
    blueprint-compiler compile lib/file_manager.blp > ui/file_manager.ui
    blueprint-compiler compile lib/window.blp > ui/window.ui
    blueprint-compiler compile lib/sidebar.blp > ui/sidebar.ui
    blueprint-compiler compile lib/webview.blp > ui/webview.ui
    blueprint-compiler compile lib/export_dialog.blp > ui/export_dialog.ui
    blueprint-compiler compile lib/search_replace.blp > ui/search_replace.ui
    blueprint-compiler compile lib/formatting_toolbar.blp > ui/formatting_toolbar.ui
    blueprint-compiler compile lib/file_manager.blp > ui/file_manager.ui

format: build-ui
    uv run ruff format .
    
check-format: format
    uv run ruff format --check
    
run: check-format
    uv run main.py

# Flatpak commands
flatpak-setup:
    echo "Setting up Flathub remote..."
    flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

flatpak-deps: flatpak-setup
    echo "Installing Flatpak dependencies..."
    flatpak install --user -y flathub org.gnome.Platform//48 org.gnome.Sdk//48 || true

flatpak-build: flatpak-deps
    echo "Building Flatpak..."
    flatpak-builder --force-clean build-dir io.github.sanjai.ProPad.yaml

flatpak-run: flatpak-build
    echo "Running Flatpak..."
    flatpak-builder --run build-dir io.github.sanjai.ProPad.yaml propad

flatpak-install: flatpak-build
    echo "Installing Flatpak locally..."
    flatpak-builder --user --install --force-clean build-dir io.github.sanjai.ProPad.yaml

flatpak-uninstall:
    echo "Uninstalling Flatpak..."
    flatpak uninstall --user -y io.github.sanjai.ProPad || true

flatpak-clean:
    echo "Cleaning Flatpak build directories..."
    rm -rf build-dir .flatpak-builder

flatpak-bundle: flatpak-build
    echo "Creating Flatpak bundle..."
    flatpak build-bundle ~/.local/share/flatpak/repo ProPad.flatpak io.github.sanjai.ProPad

# Combined workflow
flatpak-dev: flatpak-install flatpak-run

# Show logs
flatpak-logs:
    flatpak-builder --run build-dir io.github.sanjai.ProPad.yaml sh -c 'journalctl --user -f'