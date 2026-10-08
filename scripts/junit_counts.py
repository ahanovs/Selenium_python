"""Однострочная сводка по junit-отчёту pytest для CI Summary.

Использование: python scripts/junit_counts.py [путь-к-junit.xml]
Печатает человекочитаемую строку; без отчёта — честное «отчёта нет».
"""

import sys
import xml.etree.ElementTree as ET


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "reports/junit.xml"
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        print("отчёта нет — тесты не запускались или набор пуст")
        return

    suite = root if root.tag == "testsuite" else root.find("testsuite")
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


if __name__ == "__main__":
    main()
