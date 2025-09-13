import sys
from src.web.app import app, socketio
from src.cli.main import main_cli

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        main_cli()
    else:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
