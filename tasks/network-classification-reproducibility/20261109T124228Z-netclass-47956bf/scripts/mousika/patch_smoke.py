"""Validate archived parser patch in a disposable source copy, never upstream."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="mousika-patch-") as temp:
    dest=Path(temp)/"rule2entry/code"
    dest.mkdir(parents=True)
    target=dest/"rule2entry.py"
    shutil.copy2(ROOT/"upstream/mousika/rule2entry/code/rule2entry.py", target)
    subprocess.run(["patch", "-p1", "-i", str(ROOT/"patches/mousika/0001-accept-integral-decimal-class-labels.patch")], cwd=temp,check=True)
    spec=importlib.util.spec_from_file_location("patched_rule2entry",target)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parser=module.Rule2Binary()
    for label in ["1", "1.0", "0.0"]:
        source=Path(temp)/"rules.txt"
        source.write_text(" if feature_0=1.0 then "+label+"\n")
        rows=parser.parse_file(source)
        assert rows==[[1<<111,1<<111,int(float(label))]],rows
    for label in ["1.5", "NaN", "Infinity"]:
        source.write_text(" if feature_0=1.0 then "+label+"\n")
        try:
            parser.parse_file(source)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted invalid class: "+label)
    for rule in sorted((ROOT/"upstream/mousika/rule2entry/output/rule_tree/univ").glob("*.txt")):
        assert parser.parse_file(rule)==parser.load_ternary(ROOT/"upstream/mousika/rule2entry/output/ternary_entry/univ"/rule.name)
    print("PASS: integral decimal labels accepted; fractional/nonfinite labels rejected; all five bundled conversions unchanged. No upstream file changed.")
