"""Deterministic Business Identifier Generator conforming to platform nomenclature."""

class IDGenerator:
    @staticmethod
    def student_id(sequence_num: int) -> str:
        """STU-000001"""
        return f"STU-{sequence_num:06d}"

    @staticmethod
    def program_id(sequence_num: int) -> str:
        """PRG-000001"""
        return f"PRG-{sequence_num:06d}"

    @staticmethod
    def term_id(year: int, semester: str) -> str:
        """TERM-2026-FALL"""
        return f"TERM-{year}-{semester.upper()}"

    @staticmethod
    def fee_schedule_id(sequence_num: int) -> str:
        """FEE-000001"""
        return f"FEE-{sequence_num:06d}"

    @staticmethod
    def enrollment_id(sequence_num: int) -> str:
        """ENR-000001"""
        return f"ENR-{sequence_num:06d}"

    @staticmethod
    def invoice_id(student_business_id: str, year: int, sequence_num: int) -> str:
        """INV-STU-000001-2026-000001"""
        return f"INV-{student_business_id}-{year}-{sequence_num:06d}"

    @staticmethod
    def invoice_line_id(sequence_num: int) -> str:
        """INVL-000001"""
        return f"INVL-{sequence_num:06d}"

    @staticmethod
    def scholarship_id(year: int, sequence_num: int) -> str:
        """SCH-2026-000001"""
        return f"SCH-{year}-{sequence_num:06d}"

    @staticmethod
    def eligibility_id(sequence_num: int) -> str:
        """ELIG-000001"""
        return f"ELIG-{sequence_num:06d}"

    @staticmethod
    def payment_id(year: int, sequence_num: int) -> str:
        """PAY-2026-000001"""
        return f"PAY-{year}-{sequence_num:06d}"

    @staticmethod
    def allocation_id(payment_business_id: str, sequence_num: int) -> str:
        """ALLOC-PAY-2026-000001-01"""
        return f"ALLOC-{payment_business_id}-{sequence_num:02d}"

    @staticmethod
    def refund_id(year: int, sequence_num: int) -> str:
        """REF-2026-000001"""
        return f"REF-{year}-{sequence_num:06d}"

    @staticmethod
    def event_id(sequence_num: int) -> str:
        """EVT-000001"""
        return f"EVT-{sequence_num:06d}"

    @staticmethod
    def anomaly_id(sequence_num: int) -> str:
        """ANM-000001"""
        return f"ANM-{sequence_num:06d}"

    @staticmethod
    def reconciliation_run_id(sequence_num: int) -> str:
        """REC-000001"""
        return f"REC-{sequence_num:06d}"

