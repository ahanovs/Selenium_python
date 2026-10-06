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

    tests = root.get("tests", "0")
    failures = root.get("failures", "0")
    errors = root.get("errors", "0")
    skipped = root.get("skipped", "0")
    print(f"{tests} тестов: {failures} падений, {errors} ошибок, {skipped} пропущено")


if __name__ == "__main__":
    main()
