"""Reproducibility Validation Script for Deterministic Synthetic Data Generation.

Runs synthetic data generation twice with the identical seed (20261022) into two
isolated output directories, then performs an exhaustive bit-level and semantic comparison:
1. File inventory & presence
2. Exact row counts per CSV file
3. SHA-256 checksum comparison across all data files
4. Aggregate financial parity (sums of gross, net, payments, allocations, refunds)
5. Strict assertion of 100% deterministic output.
"""

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from decimal import Decimal
from typing import Any, Dict, List, Tuple


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_csv_financial_sums(filepath: str, numeric_cols: List[str]) -> Dict[str, Decimal]:
    sums = {col: Decimal("0.00") for col in numeric_cols}
    if not os.path.exists(filepath):
        return sums
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col in numeric_cols:
                if col in row and row[col]:
                    try:
                        sums[col] += Decimal(row[col])
                    except Exception:
                        pass
    return sums


class ReproducibilityValidator:
    def __init__(
        self,
        seed: int = 20261022,
        scale: str = "starter",
        dir1: str = "data/repro_run1",
        dir2: str = "data/repro_run2",
        report_path: str = "data/reproducibility_report.json"
    ):
        self.seed = seed
        self.scale = scale
        self.dir1 = dir1
        self.dir2 = dir2
        self.report_path = report_path
        self.errors: List[str] = []

    def run_generation(self, output_dir: str):
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "generate_data.py"),
            "--scale", self.scale,
            "--seed", str(self.seed),
            "--export-dir", output_dir
        ]
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        env = dict(os.environ)
        env["PYTHONPATH"] = backend_dir

        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if res.returncode != 0:
            raise RuntimeError(f"Data generation failed for {output_dir}:\n{res.stderr}\n{res.stdout}")

    def validate(self) -> Dict[str, Any]:
        print(f"=== Reproducibility Validation (Scale: {self.scale}, Seed: {self.seed}) ===")
        print(f"-> Executing Run 1 into {self.dir1}...")
        self.run_generation(self.dir1)

        print(f"-> Executing Run 2 into {self.dir2}...")
        self.run_generation(self.dir2)

        print("-> Comparing file checksums, record counts, and financial aggregates...")

        csv_files = [
            "students.csv", "programs.csv", "terms.csv", "fee_schedules.csv",
            "enrollments.csv", "scholarships.csv", "invoices.csv", "invoice_lines.csv",
            "eligibilities.csv", "payments.csv", "payment_allocations.csv",
            "refunds.csv", "financial_events.csv", "ground_truth.csv"
        ]

        file_comparisons = {}
        all_checksums_match = True

        for fname in csv_files:
            p1 = os.path.join(self.dir1, fname)
            p2 = os.path.join(self.dir2, fname)

            exists1 = os.path.exists(p1)
            exists2 = os.path.exists(p2)

            if not exists1 or not exists2:
                self.errors.append(f"File presence mismatch: {fname} (Run1={exists1}, Run2={exists2})")
                all_checksums_match = False
                continue

            h1 = compute_sha256(p1)
            h2 = compute_sha256(p2)

            # Count rows
            with open(p1, "r", encoding="utf-8") as f:
                r1_count = sum(1 for _ in f) - 1
            with open(p2, "r", encoding="utf-8") as f:
                r2_count = sum(1 for _ in f) - 1

            matches = (h1 == h2 and r1_count == r2_count)
            if not matches:
                all_checksums_match = False
                self.errors.append(f"Checksum mismatch for {fname}: hash1={h1[:8]}, hash2={h2[:8]}")

            file_comparisons[fname] = {
                "run1_sha256": h1,
                "run2_sha256": h2,
                "run1_rows": r1_count,
                "run2_rows": r2_count,
                "matches": matches,
            }

        # Compare ground_truth.json
        gt1_path = os.path.join(self.dir1, "ground_truth.json")
        gt2_path = os.path.join(self.dir2, "ground_truth.json")
        gt_h1 = compute_sha256(gt1_path)
        gt_h2 = compute_sha256(gt2_path)
        gt_matches = (gt_h1 == gt_h2)
        if not gt_matches:
            all_checksums_match = False
            self.errors.append("ground_truth.json hash mismatch between runs")

        file_comparisons["ground_truth.json"] = {
            "run1_sha256": gt_h1,
            "run2_sha256": gt_h2,
            "matches": gt_matches,
        }

        # Compare manifest counts and semantic settings (ignoring dynamic timestamp)
        m1 = json.load(open(os.path.join(self.dir1, "generation_manifest.json"), "r", encoding="utf-8"))
        m2 = json.load(open(os.path.join(self.dir2, "generation_manifest.json"), "r", encoding="utf-8"))
        manifest_match = (
            m1.get("scale") == m2.get("scale") and
            m1.get("seed") == m2.get("seed") and
            m1.get("counts") == m2.get("counts")
        )
        if not manifest_match:
            self.errors.append("Manifest counts or configurations do not match between runs")

        # Compare Financial Aggregates
        inv_sums1 = compute_csv_financial_sums(os.path.join(self.dir1, "invoices.csv"), ["gross_amount", "net_amount", "amount_paid", "outstanding_balance"])
        inv_sums2 = compute_csv_financial_sums(os.path.join(self.dir2, "invoices.csv"), ["gross_amount", "net_amount", "amount_paid", "outstanding_balance"])

        pay_sums1 = compute_csv_financial_sums(os.path.join(self.dir1, "payments.csv"), ["amount", "allocated_amount", "unallocated_amount"])
        pay_sums2 = compute_csv_financial_sums(os.path.join(self.dir2, "payments.csv"), ["amount", "allocated_amount", "unallocated_amount"])

        sch_sums1 = compute_csv_financial_sums(os.path.join(self.dir1, "scholarships.csv"), ["total_budget", "awarded_amount"])
        sch_sums2 = compute_csv_financial_sums(os.path.join(self.dir2, "scholarships.csv"), ["total_budget", "awarded_amount"])

        financial_match = (
            inv_sums1 == inv_sums2 and
            pay_sums1 == pay_sums2 and
            sch_sums1 == sch_sums2
        )
        if not financial_match:
            self.errors.append("Financial aggregate sums differ between runs")

        passed = all_checksums_match and manifest_match and financial_match and len(self.errors) == 0

        report = {
            "reproducibility_passed": passed,
            "seed": self.seed,
            "scale": self.scale,
            "all_checksums_match": all_checksums_match,
            "manifest_match": manifest_match,
            "financial_match": financial_match,
            "financial_totals": {
                "invoices_gross": str(inv_sums1.get("gross_amount", Decimal("0.00"))),
                "invoices_net": str(inv_sums1.get("net_amount", Decimal("0.00"))),
                "invoices_paid": str(inv_sums1.get("amount_paid", Decimal("0.00"))),
                "payments_total": str(pay_sums1.get("amount", Decimal("0.00"))),
                "scholarships_awarded": str(sch_sums1.get("awarded_amount", Decimal("0.00"))),
            },
            "file_comparisons": file_comparisons,
            "errors": self.errors,
        }

        os.makedirs(os.path.dirname(os.path.abspath(self.report_path)), exist_ok=True)
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"-> Reproducibility report saved to {self.report_path}")

        self._print_summary(report)
        return report

    def _print_summary(self, report: Dict[str, Any]):
        print("\n" + "=" * 65)
        print("          DETERMINISTIC REPRODUCIBILITY REPORT")
        print("=" * 65)
        status_str = "PASSED (100% BIT-IDENTICAL)" if report["reproducibility_passed"] else "FAILED"
        print(f"Overall Result          : {status_str}")
        print(f"Random Seed Tested      : {report['seed']}")
        print(f"Dataset Scale Tested    : {report['scale']}")
        print(f"All File Checksums Match: {'YES' if report['all_checksums_match'] else 'NO'}")
        print(f"Financial Totals Parity : {'YES' if report['financial_match'] else 'NO'}")
        print(f"Manifest Counts Parity  : {'YES' if report['manifest_match'] else 'NO'}")
        print("-" * 65)
        print("Key Financial Totals Verified Across Both Runs:")
        for k, v in report["financial_totals"].items():
            print(f"  - {k:<22}: INR {Decimal(v):,.2f}")
        print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Validate Deterministic Reproducibility")
    parser.add_argument("--seed", type=int, default=20261022, help="Random seed to verify")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale")
    parser.add_argument("--dir1", default="data/repro_run1", help="Output directory for Run 1")
    parser.add_argument("--dir2", default="data/repro_run2", help="Output directory for Run 2")
    parser.add_argument("--report-path", default="data/reproducibility_report.json", help="Path for JSON report")
    args = parser.parse_args()

    validator = ReproducibilityValidator(
        seed=args.seed,
        scale=args.scale,
        dir1=args.dir1,
        dir2=args.dir2,
        report_path=args.report_path
    )
    report = validator.validate()
    if not report["reproducibility_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

