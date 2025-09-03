from onbogo import create_app, cfg
import subprocess
import logging

# Force Playwright to install browser binaries at runtime
try:
    subprocess.run(["playwright", "install", "--with-deps"], check=True)
    logging.info("Playwright browsers installed successfully.")
except Exception as e:
    logging.error(f"Failed to install Playwright browsers: {e}")

app = create_app()

if __name__ == "__main__":
    app.run(host=cfg.HOST, port=cfg.PORT, use_reloader=False)
