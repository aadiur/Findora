#!/usr/bin/env python3
"""
Benchmark script for Findora search performance.

Measures exact, prefix, substring and fuzzy search times across a synthetic
dataset of 100,000 indexed filenames.

Usage:
    python tools/benchmark_search.py
"""
import sys
import os
import time
import random
import string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Findora.Backend"))
from tree import BplusTree

DATASET_SIZE = 100_000
SAMPLE_FILENAMES = [
    "Database_Notes.pdf",
    "Resume_2026.pdf",
    "Machine_Learning.pdf",
    "Project_Report.docx",
    "README.md",
    "Annual_Budget_Report_2026.xlsx",
    "Presentation_Final.pptx",
    "architecture_diagram.png",
    "source_code_backup.zip",
    "user_guide_v3.pdf",
]

def random_name(length=12):
    chars = string.ascii_letters + string.digits + "_"
    return "".join(random.choices(chars, k=length)) + ".txt"


def build_tree(n):
    t = BplusTree(order=32)
    for _ in range(n):
        t.insert(random_name(), f"/data/{random_name()}")
    for name in SAMPLE_FILENAMES:
        t.insert(name, f"/docs/{name}")
    return t


def timeit(fn, runs=5):
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return min(times), sum(times) / len(times)


def main():
    print(f"Building B+ Tree with {DATASET_SIZE:,} entries...")
    t = build_tree(DATASET_SIZE)
    print(f"Tree built.\n")
    print(f"{'Search type':<30} {'Best (ms)':>10} {'Avg (ms)':>10}")
    print("-" * 55)

    cases = [
        ("Exact match",          lambda: t.search_query("Database_Notes.pdf")),
        ("Prefix match",         lambda: t.search_query("Machine")),
        ("Substring match",      lambda: t.search_query("Budget")),
        ("Fuzzy (1 deletion)",   lambda: t.search_query("Databse_Notes.pdf")),
        ("Fuzzy (1 substitution)", lambda: t.search_query("Databese_Notes.pdf")),
        ("Fuzzy (2 deletions)",  lambda: t.search_query("Machine_Learnng.pdf")),
        ("No match (fuzzy scan)",lambda: t.search_query("zzzzzzzzz_notfound.txt")),
    ]

    for label, fn in cases:
        best, avg = timeit(fn, runs=5)
        print(f"{label:<30} {best*1000:>10.2f} {avg*1000:>10.2f}")

    print()
    print("All times in milliseconds. Best of 5 runs shown.")


if __name__ == "__main__":
    main()
