"""Rebuild the standalone offline digitiser from the same runtime CSS, JS and example."""
import base64  #: Embed the checked illustrative graph without a network dependency.
from pathlib import Path  #: Resolve matching delivered source resources deterministically.
ROOT=Path(__file__).resolve().parents[1]  #: Keep generation independent of the caller's working directory.


def build():  #: Generate the user-facing standalone page without creating an application executable.
    css=(ROOT/'web/digitiser.css').read_text()  #: Reuse the exact scoped responsive styles used by the main application.
    javascript=(ROOT/'web/digitiser.js').read_text()  #: Reuse identical calibration, checks, sessions, file actions and presentation logic.
    example=base64.b64encode((ROOT/'data/digitiser-example.png').read_bytes()).decode('ascii')  #: Preserve the actual illustrative PNG as embedded offline data.
    prefix='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Magnetics Studio 0.9.2 · B–H image digitiser</title><style>body{margin:0;padding:32px;background:#101c2b;color:#dce8f5;font:14px/1.6 system-ui}body>h1{font-size:25px}body>button{padding:10px 16px;border:1px solid #7e9cb9;border-radius:6px;background:#edaa6d;color:#17283a;cursor:pointer}[hidden]{display:none!important}\n'  #: Give the local launcher minimal independent styling without importing the application shell.
    launcher='</style></head><body><h1>B–H image digitiser · 0.9.2</h1><p>Load a graph, calibrate its axes and trace one curve. Images and sessions stay on this device. No Python or internet connection is needed.</p><button id="reopen" type="button">Open digitiser</button><script>\n'  #: Provide an accessible reopen action for a closed standalone modal.
    bootstrap="\nconst digitiser=new MagneticsImageDigitiser({exampleSrc:'data:image/png;base64,"+example+"'}); // #: Use the same digitiser implementation with an embedded illustrative example.\ndocument.getElementById('reopen').addEventListener('click',()=>digitiser.open()); // #: Reopen the local native dialog without discarding its current session.\ndigitiser.open(); // #: Start the standalone page in the same usable empty state as the application.\n"  #: Keep standalone bootstrap explicit and its executable lines individually explained.
    page=prefix+css+launcher+javascript+bootstrap+'</script></body></html>\n'  #: Embed exact shared resources so opening the HTML requires no server or external asset.
    target=ROOT/'Image_BH_Digitiser.html'  #: Preserve the existing standalone deliverable's stable filename.
    target.write_text(page)  #: Replace only the generated offline digitiser output.
    return target  #: Allow deterministic regeneration to be checked by tests and release tooling.


if __name__=='__main__':  #: Generate only through an explicit source-form invocation.
    print(build())  #: Report the completed standalone artifact path.
