from server import init_app

app = init_app()
debug = True

if __name__=='__main__':
    app.run(debug=debug)
