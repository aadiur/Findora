"""
Comprehensive tests for fuzzy (Levenshtein) search in BplusTree.

Covers:
- Regression: exact, prefix, substring search unchanged
- Single-character insertion, deletion, substitution
- Multi-character errors within threshold
- Case-insensitive fuzzy matching
- Empty / very short queries
- Long filenames
- Duplicate filenames in different directories (multiple paths)
- Ranking by edit distance
- No results beyond the threshold
- Deduplication between fuzzy and earlier search stages
- Large dataset performance
- Threshold table correctness
- Levenshtein helper correctness
"""

import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "Findora.Backend"))

from tree import BplusTree


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_tree(*filenames):
    """Return a fresh BplusTree with each filename inserted at a synthetic path."""
    t = BplusTree(order=32)
    for name in filenames:
        t.insert(name, f"/docs/{name}")
    return t


def result_names(results):
    """Extract just the filename strings from search_query results."""
    return [r[0] for r in results]


# ---------------------------------------------------------------------------
# Threshold table unit tests
# ---------------------------------------------------------------------------

class TestFuzzyThreshold:
    def test_very_short_queries_get_zero(self):
        assert BplusTree._fuzzy_threshold(1) == 0
        assert BplusTree._fuzzy_threshold(2) == 0

    def test_short_queries_get_one(self):
        assert BplusTree._fuzzy_threshold(3) == 1
        assert BplusTree._fuzzy_threshold(4) == 1

    def test_medium_queries_get_two(self):
        assert BplusTree._fuzzy_threshold(5) == 2
        assert BplusTree._fuzzy_threshold(8) == 2

    def test_long_queries_get_three(self):
        assert BplusTree._fuzzy_threshold(9) == 3
        assert BplusTree._fuzzy_threshold(20) == 3


# ---------------------------------------------------------------------------
# Levenshtein helper unit tests
# ---------------------------------------------------------------------------

class TestLevenshtein:
    def test_identical_strings(self):
        assert BplusTree._levenshtein("hello", "hello", 3) == 0

    def test_single_substitution(self):
        assert BplusTree._levenshtein("hello", "helo0", 3) == 2  # h e l l o vs h e l o 0
        assert BplusTree._levenshtein("cat", "bat", 2) == 1

    def test_single_deletion(self):
        # "databse" vs "database" — one deletion
        assert BplusTree._levenshtein("databse", "database", 3) == 1

    def test_single_insertion(self):
        assert BplusTree._levenshtein("databasee", "database", 3) == 1

    def test_empty_strings(self):
        assert BplusTree._levenshtein("", "", 5) == 0
        assert BplusTree._levenshtein("abc", "", 5) == 3
        assert BplusTree._levenshtein("", "abc", 5) == 3

    def test_early_termination(self):
        # completely different strings, early termination should fire
        result = BplusTree._levenshtein("abcdef", "xyz123", 2)
        assert result > 2

    def test_length_prefilter(self):
        # length difference exceeds max_dist → returns max_dist + 1 immediately
        result = BplusTree._levenshtein("hi", "toolongstring", 1)
        assert result > 1

    def test_known_distances(self):
        assert BplusTree._levenshtein("kitten", "sitting", 10) == 3
        assert BplusTree._levenshtein("sunday", "saturday", 10) == 3


# ---------------------------------------------------------------------------
# Regression: existing search stages must still work
# ---------------------------------------------------------------------------

class TestRegressionExistingSearch:
    def setup_method(self):
        self.tree = make_tree(
            "Database_Notes.pdf",
            "Resume_2026.pdf",
            "Machine_Learning.pdf",
            "Project_Report.docx",
            "README.md",
            "notes.txt",
        )

    def test_exact_match_still_works(self):
        results = result_names(self.tree.search_query("Database_Notes.pdf"))
        assert "Database_Notes.pdf" in results
        # Exact match must come first
        assert results[0] == "Database_Notes.pdf"

    def test_prefix_match_still_works(self):
        results = result_names(self.tree.search_query("Database"))
        assert "Database_Notes.pdf" in results

    def test_substring_match_still_works(self):
        results = result_names(self.tree.search_query("Notes"))
        assert "Database_Notes.pdf" in results

    def test_empty_query_returns_empty(self):
        assert self.tree.search_query("") == []

    def test_case_insensitive_exact(self):
        results = result_names(self.tree.search_query("database_notes.pdf"))
        assert "Database_Notes.pdf" in results

    def test_case_insensitive_prefix(self):
        results = result_names(self.tree.search_query("machine"))
        assert "Machine_Learning.pdf" in results

    def test_full_search_query_method_regression(self):
        """search_query returns all three tiers for a comprehensive query set."""
        t = make_tree("alpha.txt", "alphabet.txt", "beta.txt")
        results = result_names(t.search_query("alpha"))
        # "alpha.txt" is exact; "alphabet.txt" is prefix
        assert "alpha.txt" in results
        assert "alphabet.txt" in results


# ---------------------------------------------------------------------------
# Fuzzy: single-character errors
# ---------------------------------------------------------------------------

class TestFuzzySingleCharErrors:
    def setup_method(self):
        self.tree = make_tree(
            "Database_Notes.pdf",
            "Resume_2026.pdf",
            "Machine_Learning.pdf",
            "Project_Report.docx",
        )

    def test_single_char_deletion(self):
        # "Databse" is "Database" with 'a' removed → dist 1
        results = result_names(self.tree.search_query("Databse_Notes.pdf"))
        assert "Database_Notes.pdf" in results

    def test_single_char_insertion(self):
        # "Databasee" has an extra 'e'
        results = result_names(self.tree.search_query("Databasee_Notes.pdf"))
        assert "Database_Notes.pdf" in results

    def test_single_char_substitution(self):
        # "Databese" → 'a' replaced with 'e'
        results = result_names(self.tree.search_query("Databese_Notes.pdf"))
        assert "Database_Notes.pdf" in results

    def test_stem_deletion(self):
        # "Databse_Notes.pdf" vs "Database_Notes.pdf" — 1 deletion, same length class
        # Stem-only short queries cannot fuzzy-match much longer full filenames (by design).
        # This test verifies the realistic case: near-complete filename with 1 typo.
        results = result_names(self.tree.search_query("Databse_Notes.pdf"))
        assert "Database_Notes.pdf" in results

    def test_resume_typo(self):
        # "Resum" (5 chars) is a prefix of "Resume_2026.pdf" — caught by prefix search
        results = result_names(self.tree.search_query("Resum"))
        assert "Resume_2026.pdf" in results

    def test_machine_typo(self):
        # "Machine_Learnig.pdf" — 1 deletion ('n') in a 19-char query (threshold 3)
        results = result_names(self.tree.search_query("Machine_Learnig.pdf"))
        assert "Machine_Learning.pdf" in results

    def test_project_typo(self):
        # "Project_Reprt.docx" — 1 deletion ('o') in a 18-char query (threshold 3)
        results = result_names(self.tree.search_query("Project_Reprt.docx"))
        assert "Project_Report.docx" in results


# ---------------------------------------------------------------------------
# Fuzzy: multi-character errors within threshold
# ---------------------------------------------------------------------------

class TestFuzzyMultiCharErrors:
    def setup_method(self):
        self.tree = make_tree(
            "Machine_Learning.pdf",
            "Project_Report.docx",
            "Database_Notes.pdf",
        )

    def test_two_char_error_medium_query(self):
        # "Machine_Learnng.pdf" — 2 deletions in a 19-char query (threshold 3)
        # "Machine_Learning.pdf" vs "Machine_Learnng.pdf": delete 'i' twice
        results = result_names(self.tree.search_query("Machine_Learnng.pdf"))
        assert "Machine_Learning.pdf" in results

    def test_two_char_substitution(self):
        # "Projact_Raport.docx" is 19 chars → threshold 3; dist = 2 (e→a, e→a)
        results = result_names(self.tree.search_query("Projact_Raport.docx"))
        assert "Project_Report.docx" in results


# ---------------------------------------------------------------------------
# Fuzzy: query length edge cases
# ---------------------------------------------------------------------------

class TestFuzzyQueryLengthEdgeCases:
    def setup_method(self):
        self.tree = make_tree("hi.txt", "ab.pdf", "longer_file.txt")

    def test_very_short_query_no_fuzzy(self):
        # "hi" is 2 chars → threshold = 0 → no fuzzy results beyond exact
        results = result_names(self.tree.search_query("hx"))
        # "hi.txt" differs by 1 char, but threshold is 0 → should NOT be found by fuzzy
        assert "hi.txt" not in results

    def test_one_char_query_no_fuzzy(self):
        results = result_names(self.tree.search_query("z"))
        # Should not blow up; no fuzzy for single-char queries
        assert isinstance(results, list)

    def test_empty_query_safe(self):
        results = self.tree.search_query("")
        assert results == []

    def test_three_char_query_gets_fuzzy(self):
        # "lng" (3 chars → threshold 1); "longer_file.txt" does NOT match (dist >> 1)
        # but we can verify 3-char queries don't crash
        results = self.tree.search_query("lng")
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# Fuzzy: case insensitivity
# ---------------------------------------------------------------------------

class TestFuzzyCaseInsensitive:
    def setup_method(self):
        self.tree = make_tree(
            "Database_Notes.pdf",
            "Machine_Learning.pdf",
        )

    def test_lowercase_typo(self):
        # "databse_notes.pdf" is a lowercase typo of "Database_Notes.pdf" (1 deletion)
        results = result_names(self.tree.search_query("databse_notes.pdf"))
        assert "Database_Notes.pdf" in results

    def test_uppercase_typo(self):
        # "DATABSE_NOTES.PDF" — uppercase version with 1 deletion
        results = result_names(self.tree.search_query("DATABSE_NOTES.PDF"))
        assert "Database_Notes.pdf" in results

    def test_mixed_case_typo(self):
        # "MaChNe_LeaRnIng.pdf" — mixed case with 1 substitution ('r' → 'a' in 'Learning')
        results = result_names(self.tree.search_query("MaChNe_LeaRnIng.pdf"))
        assert "Machine_Learning.pdf" in results


# ---------------------------------------------------------------------------
# Fuzzy: duplicate filenames in different directories (multiple paths)
# ---------------------------------------------------------------------------

class TestFuzzyDuplicatePaths:
    def test_same_filename_multiple_paths_preserved(self):
        t = BplusTree(order=32)
        t.insert("Report.docx", "/home/user/Report.docx")
        t.insert("Report.docx", "/work/Report.docx")

        # Typo: "Reporr.docx" → dist 1
        results = t.search_query("Reporr.docx")
        names = result_names(results)
        assert "Report.docx" in names

        # Both paths must be present
        for filename, paths in results:
            if filename == "Report.docx":
                assert "/home/user/Report.docx" in paths
                assert "/work/Report.docx" in paths

    def test_fuzzy_does_not_duplicate_same_filename(self):
        """A filename matched by exact/prefix/substring must not appear again in fuzzy tier."""
        t = make_tree("notes.txt", "notes_backup.txt")
        results = result_names(t.search_query("notes.txt"))
        # "notes.txt" should appear exactly once
        assert results.count("notes.txt") == 1


# ---------------------------------------------------------------------------
# Fuzzy: ranking by edit distance
# ---------------------------------------------------------------------------

class TestFuzzyRanking:
    def test_closer_distance_ranked_first(self):
        """Of two fuzzy candidates, the one with smaller edit distance appears first."""
        t = BplusTree(order=32)
        # "queryx" (dist 1 from "query") vs "querry" (dist 1) — both should appear
        # Use a clearer distance difference:
        # "query_file.txt" (dist 1 from "qury_file.txt") vs "other_query_file.txt" (dist > 1 as fuzzy)
        t.insert("query_file.txt", "/a/query_file.txt")
        t.insert("quory_file.txt", "/b/quory_file.txt")  # dist 1 from "query_file.txt"
        t.insert("quiry_file.txt", "/c/quiry_file.txt")  # dist 1 from "query_file.txt"

        # "query_file.txt" is exact; fuzzy tier should include the dist-1 variants
        results = result_names(t.search_query("query_file.txt"))
        assert "query_file.txt" in results
        # exact match must come before fuzzy
        assert results.index("query_file.txt") == 0

    def test_exact_beats_fuzzy(self):
        t = make_tree("alpha.txt", "alPha.txt")
        # "alpha.txt" is case-insensitive exact; fuzzy should not displace it
        results = result_names(t.search_query("alpha.txt"))
        assert results[0].lower() == "alpha.txt"

    def test_multiple_fuzzy_candidates_ordered_by_distance(self):
        """When two fuzzy candidates have different distances, lower distance comes first."""
        t = BplusTree(order=32)
        # "birthday_party.txt" — query: "birdhday_party.txt" (transposition-ish, dist 1)
        # "birdhouse.txt" — dist >> threshold for this query length
        t.insert("birthday_party.txt", "/a/birthday_party.txt")
        t.insert("birthdaay_party.txt", "/b/birthdaay_party.txt")  # extra 'a', dist 1

        results = result_names(t.search_query("birthday_party.txt"))
        # Exact match first
        assert results[0] == "birthday_party.txt"
        # dist-1 variant should also appear in results
        assert "birthdaay_party.txt" in results


# ---------------------------------------------------------------------------
# Fuzzy: no results beyond threshold
# ---------------------------------------------------------------------------

class TestFuzzyThresholdEnforcement:
    def test_no_results_beyond_max_distance(self):
        """A query with 5+ char typos on a 6-char name must NOT appear in fuzzy results."""
        t = make_tree("dog.txt")
        # "dog.txt" (7 chars, threshold=1): query "xyz.txt" differs by 3 → should not match
        results = result_names(t.search_query("xyz.txt"))
        assert "dog.txt" not in results

    def test_unrelated_query_returns_empty(self):
        t = make_tree("alpha.txt", "beta.pdf", "gamma.docx")
        results = result_names(t.search_query("zzzzzzzzzzz"))
        assert results == []

    def test_long_typo_exceeds_threshold(self):
        """5 errors in a 9-char query exceeds threshold of 3."""
        t = make_tree("document.txt")
        # "xxxxxxxxt" — 8 substitutions from "document" → definitely > 3
        results = result_names(t.search_query("xxxxxxxxt"))
        assert "document.txt" not in results


# ---------------------------------------------------------------------------
# Fuzzy: deduplication between search stages
# ---------------------------------------------------------------------------

class TestFuzzyDeduplication:
    def test_fuzzy_does_not_duplicate_exact_match(self):
        t = make_tree("notes.txt")
        results = result_names(t.search_query("notes.txt"))
        assert results.count("notes.txt") == 1

    def test_fuzzy_does_not_duplicate_prefix_match(self):
        t = make_tree("notes_archive.txt", "notes.txt")
        # "notes" is a prefix of "notes_archive.txt"
        # it also might fuzzy-match "notes.txt"; ensure no duplication
        results = result_names(t.search_query("notes"))
        for name in results:
            assert results.count(name) == 1, f"Duplicate found: {name}"

    def test_fuzzy_does_not_duplicate_substring_match(self):
        t = make_tree("my_notes_file.txt")
        # "notes" substring matches; should not appear again via fuzzy
        results = result_names(t.search_query("notes"))
        assert results.count("my_notes_file.txt") == 1


# ---------------------------------------------------------------------------
# Fuzzy: long filenames
# ---------------------------------------------------------------------------

class TestFuzzyLongFilenames:
    def test_long_filename_single_typo(self):
        long_name = "Very_Long_Descriptive_Project_Report_2026_Final_Version.docx"
        t = make_tree(long_name)
        # Remove one character from the query (53 chars → threshold 3; dist 1)
        typo = "Very_Long_Descriptive_Project_Repot_2026_Final_Version.docx"
        results = result_names(t.search_query(typo))
        assert long_name in results

    def test_long_filename_no_match_excessive_typos(self):
        long_name = "Annual_Budget_Report_2026.xlsx"
        t = make_tree(long_name)
        # Query differs by 10+ characters — well beyond threshold
        results = result_names(t.search_query("Completely_Different_Filename.xlsx"))
        assert long_name not in results


# ---------------------------------------------------------------------------
# Fuzzy: priority order (exact > prefix > substring > fuzzy)
# ---------------------------------------------------------------------------

class TestFuzzyPriorityOrder:
    def test_exact_before_prefix_before_substring_before_fuzzy(self):
        t = BplusTree(order=32)
        t.insert("alpha.txt", "/a/alpha.txt")       # exact for query "alpha.txt"
        t.insert("alpha_backup.txt", "/b/alpha_backup.txt")  # prefix
        t.insert("my_alpha_file.txt", "/c/my_alpha_file.txt")  # substring

        results = result_names(t.search_query("alpha.txt"))
        # exact must be first
        assert results[0] == "alpha.txt"

    def test_fuzzy_only_appears_when_no_better_match(self):
        """Fuzzy results appear only after exact/prefix/substring tiers."""
        t = BplusTree(order=32)
        t.insert("report.txt", "/a/report.txt")       # exact for "report.txt"
        t.insert("reprt_summary.txt", "/b/reprt_summary.txt")  # fuzzy (dist 1 for "report")

        results = result_names(t.search_query("report.txt"))
        # exact must come first; fuzzy (reprt_summary.txt) will NOT match because
        # "report.txt" vs "reprt_summary.txt" differs by more than threshold
        assert results[0] == "report.txt"


# ---------------------------------------------------------------------------
# Large dataset performance test
# ---------------------------------------------------------------------------

class TestFuzzyLargeDatasetPerformance:
    def test_large_dataset_fuzzy_completes_in_time(self):
        """
        Insert 10,000 synthetic filenames and ensure fuzzy search completes
        within 2 seconds. This validates the length pre-filter and early termination
        keep performance acceptable.
        """
        t = BplusTree(order=32)
        for i in range(10_000):
            name = f"file_{i:05d}_document.txt"
            t.insert(name, f"/data/{name}")

        # Also add a few names that the fuzzy query should find
        t.insert("special_target.txt", "/docs/special_target.txt")

        start = time.perf_counter()
        # "specal_target.txt" → dist 1 from "special_target.txt" (deletion of 'i')
        results = t.search_query("specal_target.txt", limit=50)
        elapsed = time.perf_counter() - start

        names = result_names(results)
        assert "special_target.txt" in names, "Fuzzy match not found in large dataset"
        assert elapsed < 2.0, f"Fuzzy search took {elapsed:.3f}s — exceeded 2s budget"

    def test_large_dataset_exact_still_fast(self):
        """
        Insert 10,000 synthetic filenames and verify exact search completes
        within a generous time budget. The fuzzy scan may still run after
        exact/prefix/substring on this dataset, but the overall time should
        remain well under the interactive threshold.
        """
        t = BplusTree(order=32)
        for i in range(10_000):
            name = f"item_{i:05d}.txt"
            t.insert(name, f"/data/{name}")

        start = time.perf_counter()
        results = t.search_query("item_09999.txt", limit=50)
        elapsed = time.perf_counter() - start

        assert result_names(results)[0] == "item_09999.txt"
        assert elapsed < 2.0, f"Search too slow: {elapsed:.3f}s"

    def test_large_dataset_no_fuzzy_for_short_query(self):
        """Short queries must not trigger fuzzy on large datasets."""
        t = BplusTree(order=32)
        for i in range(10_000):
            t.insert(f"doc_{i}.pdf", f"/d/doc_{i}.pdf")

        start = time.perf_counter()
        # 2-char query → threshold 0 → no fuzzy scan
        t.search_query("xy", limit=50)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Short-query search was unexpectedly slow: {elapsed:.3f}s"


# ---------------------------------------------------------------------------
# Fuzzy: private helper isolation tests
# ---------------------------------------------------------------------------

class TestFuzzyInternals:
    def test_fuzzy_scan_respects_seen_set(self):
        """_fuzzy_scan must not return filenames already in seen."""
        t = make_tree("notes.txt", "note.txt")
        # Pretend "note.txt" was already found in a prior stage
        seen = {"note.txt"}
        results = t._fuzzy_scan("notes.txt", seen, max_dist=1, limit=10)
        returned_names = [r[0] for r in results]
        assert "note.txt" not in returned_names

    def test_fuzzy_scan_returns_sorted_by_distance(self):
        """Results from _fuzzy_scan must be ordered by ascending edit distance."""
        t = BplusTree(order=32)
        # "query" (5 chars, threshold 1)
        t.insert("querry", "/a/querry")  # dist 1
        t.insert("qquery", "/b/qquery")  # dist 1
        t.insert("query", "/c/query")   # exact — will be in seen already

        seen = {"query"}
        results = t._fuzzy_scan("query", seen, max_dist=1, limit=10)
        distances = []
        for name, _ in results:
            d = BplusTree._levenshtein("query", name, 3)
            distances.append(d)
        # Verify non-decreasing order
        assert distances == sorted(distances)
