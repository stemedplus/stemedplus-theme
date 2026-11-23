"""Check that every HuMeta discipline term the STEMEd+ discipline list uses exists in the
HuMeta profile and is not deprecated.

    python check_humeta_terms.py                    # against humeta-profile's main branch
    python check_humeta_terms.py path/to/vocabularies.json

The list in stemedplus_disciplines.json maps each discipline to HuMeta (ANZSRC 2020) terms, which
are kept in humeta-profile's vocabularies.json. The Tests workflow runs this on every pull request
and once a week, so a term removed or deprecated in HuMeta is caught here. Exit status 1 means a
problem was found; 2 means the vocabulary could not be read.
"""
import json
import sys
import urllib.request
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
LIST = HERE / "stemedplus_disciplines.json"
VOCABULARIES_URL = "https://raw.githubusercontent.com/stemedplus/humeta-profile/main/vocabularies.json"


def problems(disciplines: dict, vocabularies: dict) -> List[str]:
    terms = {t["id"]: t for t in vocabularies["vocabularies"]["discipline"]["terms"]}
    found = []
    for d in disciplines["disciplines"]:
        for code in d["humeta_disciplines"]:
            if code not in terms:
                found.append(f"{d['id']}: {code} is not a HuMeta discipline term")
            elif terms[code].get("deprecated"):
                found.append(f"{d['id']}: {code} is deprecated in HuMeta")
    return found


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        if argv:
            vocabularies = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
        else:
            with urllib.request.urlopen(VOCABULARIES_URL, timeout=60) as response:
                vocabularies = json.load(response)
    except Exception as error:  # noqa: BLE001
        print(f"Could not read the HuMeta vocabularies ({type(error).__name__}: {error})")
        return 2
    found = problems(json.loads(LIST.read_text(encoding="utf-8")), vocabularies)
    for p in found:
        print(p)
    print(f"{len(found)} problem(s) with the HuMeta discipline terms.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
