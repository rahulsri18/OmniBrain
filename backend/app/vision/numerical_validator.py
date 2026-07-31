"""
Numerical Validation Parser for Vision Model Outputs.
Extracts numbers, percentages, and table data from vision OCR/LLM responses,
and performs arithmetic integrity and boundary validation.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class NumericalValidationResult:
    is_valid: bool
    extracted_numbers: List[float] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    table_integrity_passed: Optional[bool] = None
    summary: str = ""


class VisionNumericalValidator:
    """
    Parser to extract and mathematically validate numerical values
    from vision model output text and markdown tables.
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        tolerance: float = 1e-2,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.tolerance = tolerance

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """
        Extracts all standalone integers, floats, percentages, and formatted currency values from text.
        """
        if not text:
            return []

        # Matches numbers including currency signs, commas, decimals, and percentages
        pattern = r"[-+]?\b(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
        matches = re.findall(pattern, text)

        cleaned_numbers: List[float] = []
        for match in matches:
            try:
                val_str = match.replace(",", "").replace("%", "").strip()
                cleaned_numbers.append(float(val_str))
            except ValueError:
                continue

        return cleaned_numbers

    @classmethod
    def parse_markdown_table(cls, text: str) -> List[List[str]]:
        """
        Parses Markdown table structures from the vision model text into a 2D matrix.
        """
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        table_rows = []

        for line in lines:
            if "|" in line:
                # Ignore table header delimiter lines (e.g., |---|---|)
                if re.match(r"^\|?\s*:?-+:?\s*(\|?\s*:?-+:?\s*)+\|?$", line):
                    continue
                row = [cell.strip() for cell in line.split("|")]
                # Strip edge empty elements resulting from leading/trailing pipes
                if row and row[0] == "":
                    row.pop(0)
                if row and row[-1] == "":
                    row.pop(-1)
                if row:
                    table_rows.append(row)

        return table_rows

    def validate_sum_integrity(
        self, values: List[float], expected_sum: float
    ) -> Tuple[bool, str]:
        """
        Checks if a list of numbers sums up to an expected total within tolerance.
        """
        calculated_sum = sum(values)
        diff = abs(calculated_sum - expected_sum)
        if diff <= self.tolerance:
            return True, f"Sum match valid: {calculated_sum:.2f} == {expected_sum:.2f}"
        
        return False, f"Sum mismatch: calculated {calculated_sum:.2f}, expected {expected_sum:.2f} (diff: {diff:.2f})"

    def validate_boundaries(self, numbers: List[float]) -> List[str]:
        """
        Validates that extracted numbers fall within expected min/max boundaries.
        """
        errors = []
        for num in numbers:
            if self.min_value is not None and num < self.min_value:
                errors.append(f"Value {num} is below min boundary {self.min_value}")
            if self.max_value is not None and num > self.max_value:
                errors.append(f"Value {num} exceeds max boundary {self.max_value}")
        return errors

    def validate_vision_output(
        self,
        text: str,
        expected_total: Optional[float] = None,
        check_table: bool = True,
    ) -> NumericalValidationResult:
        """
        Main execution flow to parse and validate vision model output.
        """
        errors: List[str] = []
        extracted_nums = self.extract_numbers(text)

        if not extracted_nums and not text.strip():
            return NumericalValidationResult(
                is_valid=False,
                validation_errors=["Empty text input received."],
                summary="Validation failed due to empty input.",
            )

        # 1. Boundary Checks
        boundary_errors = self.validate_boundaries(extracted_nums)
        errors.extend(boundary_errors)

        # 2. Total Sum Validation (if target sum is provided)
        if expected_total is not None and extracted_nums:
            # Exclude the total itself if it's included at the end of the extracted list
            sub_list = extracted_nums[:-1] if extracted_nums[-1] == expected_total else extracted_nums
            is_sum_ok, sum_msg = self.validate_sum_integrity(sub_list, expected_total)
            if not is_sum_ok:
                errors.append(sum_msg)

        # 3. Table Column/Row Numerical Integrity Check
        table_passed: Optional[bool] = None
        if check_table:
            table = self.parse_markdown_table(text)
            if len(table) >= 2:
                table_passed = True
                # Attempt to validate if the bottom row represents column totals
                last_row = table[-1]
                for col_idx in range(len(last_row)):
                    try:
                        total_val = float(last_row[col_idx].replace(",", "").replace("%", ""))
                        col_vals = []
                        for row in table[:-1]:
                            if col_idx < len(row):
                                val_str = row[col_idx].replace(",", "").replace("%", "")
                                if re.match(r"^[-+]?\d+(\.\d+)?$", val_str):
                                    col_vals.append(float(val_str))
                        
                        if col_vals:
                            ok, msg = self.validate_sum_integrity(col_vals, total_val)
                            if not ok:
                                table_passed = False
                                errors.append(f"Table col {col_idx} error: {msg}")
                    except ValueError:
                        continue

        is_valid = len(errors) == 0

        return NumericalValidationResult(
            is_valid=is_valid,
            extracted_numbers=extracted_nums,
            validation_errors=errors,
            table_integrity_passed=table_passed,
            summary="Numerical validation passed successfully." if is_valid else f"Validation failed with {len(errors)} error(s).",
        )