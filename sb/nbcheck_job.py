"""sb.nbcheck as a scheduler job (sb.memsched.module_job needs a result file): runs the check and writes its last line,
or the reason it stopped, to --result.

    python -m sb.nbcheck_job --result D:/.../nbcheck_v15.txt -- --notebook ... --policy ... --params ... --scenario ...
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

from sb import nbcheck


def main() -> None:
    i = sys.argv.index("--")
    result = Path(sys.argv[sys.argv.index("--result") + 1])
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            nbcheck.main(sys.argv[i + 1:])
        line = buf.getvalue().strip().splitlines()[-1]
    except SystemExit as e:
        line = f"FAILED: {e}"
    except AssertionError as e:
        line = f"FAILED: {e}"
    print(line, flush=True)
    result.write_text(line + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
