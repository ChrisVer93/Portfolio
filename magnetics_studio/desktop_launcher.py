"""Double-clickable desktop entry and isolated frozen native worker entry."""
import json  #: Keep native worker requests/results finite and source-compatible.
import multiprocessing  #: Register the standard frozen-process startup guard.
from pathlib import Path  #: Read only explicit parent-generated worker paths.
import sys  #: Distinguish the private worker entry from the normal local GUI.


def main():  #: Reuse the original source application and its native worker in a frozen executable.
    multiprocessing.freeze_support()  #: Prevent frozen multiprocessing helpers from starting another GUI.
    if len(sys.argv)>1 and sys.argv[1]=='--backend-worker':  #: Dispatch an isolated operation instead of interpreting the executable as Python.
        if len(sys.argv)!=5:raise ValueError('Invalid private worker arguments')  #: Reject incomplete native process requests.
        from tools.backend_worker import execute  #: Preserve the original whitelisted optional-native implementation.
        result=execute(sys.argv[2],json.loads(Path(sys.argv[3]).read_text(encoding='utf-8')))  #: Execute exactly the parent-written request through existing native preflight.
        Path(sys.argv[4]).write_text(json.dumps(result,allow_nan=False),encoding='utf-8')  #: Publish only a complete finite worker result.
    else:  #: Keep normal launch and existing command-line arguments source-compatible.
        from studio import main as launch  #: Resolve original browser interface and bundled resource paths.
        launch()  #: Start the actual local server and default browser.


if __name__=='__main__':main()  #: Keep imported launcher helpers free of native work.
