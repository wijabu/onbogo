from onbogo import create_app, cfg

app = create_app()

if __name__ == "__main__":
    app.run(host=cfg.HOST, port=cfg.PORT, use_reloader=False)
