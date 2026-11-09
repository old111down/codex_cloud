"""Execute the same source/arguments after the explicitly recorded import aliases."""
import runpy
import sys
from pathlib import Path
import compat_bootstrap
target=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(target.parent))
sys.argv=sys.argv[1:]
runpy.run_path(str(target),run_name='__main__')
