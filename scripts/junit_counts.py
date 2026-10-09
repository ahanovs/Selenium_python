"""Однострочная сводка по junit-отчёту pytest для CI Summary.

Использование:
  python scripts/junit_counts.py [путь-к-junit.xml]            — строка «прошло N из M…»
  python scripts/junit_counts.py --failures [путь]             — то же + список упавших тестов
                                                               (имя + первая строка ошибки)
Без отчёта — честное «отчёта нет».
"""

import sys
import xml.etree.ElementTree as ET

MAX_NAME = 70
MAX_ERROR = 200


def _suite(path):
    root = ET.parse(path).getroot()
    return root if root.tag == "testsuite" else root.find("testsuite")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    failures_mode = "--failures" in sys.argv[1:]
    path = args[0] if args else "reports/junit.xml"

    try:
        suite = _suite(path)
    except (OSError, ET.ParseError):
        print("отчёта нет — тесты не запускались или набор пуст")
        return
    if suite is None:
        print("отчёта нет — неожиданный формат junit")
        return

    tests = int(suite.get("tests", "0"))
    failures = int(suite.get("failures", "0"))
    errors = int(suite.get("errors", "0"))
    skipped = int(suite.get("skipped", "0"))

    if tests == 0:
        print("набор пуст (0 тестов)")
        return

    passed = tests - failures - errors - skipped
    print(f"прошло {passed} из {tests}: падений {failures}, ошибок {errors}, пропущено {skipped}")

    if not failures_mode:
        return

    shown = 0
    for case in suite.iter("testcase"):
        fail = case.find("failure") or case.find("error")
        if fail is None:
            continue
        name = case.get("name", "?")
        if len(name) > MAX_NAME:
            name = name[: MAX_NAME - 1] + "…"
        first_error = ""
        for line in (fail.text or "").splitlines():
            line = line.strip()
            if line.startswith("E "):
                first_error = line
                break
        if len(first_error) > MAX_ERROR:
            first_error = first_error[: MAX_ERROR - 1] + "…"
        print(f"УПАЛ {name}")
        if first_error:
            print(f"  {first_error}")
        shown += 1
    if shown == 0:
        print("в отчёте нет деталей падений")


if __name__ == "__main__":
    main()
