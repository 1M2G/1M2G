from __future__ import annotations
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


# ============================================================
# DEPARTMENT
# ============================================================

class Department(Enum):
    PRODUCTION = "Production"
    OPERATIONS = "Operations and Monitoring"
    ADMINISTRATION = "Administration"
    NOT_ELIGIBLE = "Not eligible for placement"


# ============================================================
# WORKER MODEL
# ============================================================

@dataclass
class Worker:
    worker_id: int
    name: str
    address: str
    phone: str
    age: int

    @property
    def department(self) -> Department:
        """Automatically determine the worker's department."""

        if 18 <= self.age <= 35:
            return Department.PRODUCTION

        if 36 <= self.age <= 40:
            return Department.OPERATIONS

        if 41 <= self.age <= 55:
            return Department.ADMINISTRATION

        return Department.NOT_ELIGIBLE

    @property
    def eligible(self) -> bool:
        """Return whether the worker is eligible for placement."""
        return self.department != Department.NOT_ELIGIBLE

    def update(
        self,
        name: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        age: Optional[int] = None,
    ) -> None:
        """Update worker information without replacing the entire object."""

        if name is not None:
            self.name = name

        if address is not None:
            self.address = address

        if phone is not None:
            self.phone = phone

        if age is not None:
            self.age = age

    def to_dict(self) -> dict:
        """Convert worker to a JSON-compatible dictionary."""

        data = asdict(self)
        data["department"] = self.department.value
        data["eligible"] = self.eligible

        return data

    def display(self) -> None:
        """Display worker information."""

        print("\n" + "-" * 55)
        print(f"Worker ID    : {self.worker_id}")
        print(f"Name         : {self.name}")
        print(f"Address      : {self.address}")
        print(f"Phone        : {self.phone}")
        print(f"Age          : {self.age}")
        print(f"Department   : {self.department.value}")
        print(f"Eligibility  : {'Eligible' if self.eligible else 'Not Eligible'}")
        print("-" * 55)


# ============================================================
# VALIDATION
# ============================================================

class Validator:

    @staticmethod
    def validate_name(name: str) -> str:
        """Validate and normalize a worker's name."""

        name = name.strip()

        if not name:
            raise ValueError("Name cannot be empty.")

        if len(name) < 2:
            raise ValueError("Name must contain at least 2 characters.")

        if not re.fullmatch(r"[A-Za-zÀ-ÿ\s'-]+", name):
            raise ValueError(
                "Name can only contain letters, spaces, apostrophes and hyphens."
            )

        return " ".join(name.split()).title()

    @staticmethod
    def validate_address(address: str) -> str:
        """Validate worker address."""

        address = address.strip()

        if not address:
            raise ValueError("Address cannot be empty.")

        return address

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate a Ugandan-style phone number."""

        phone = phone.strip()

        # Allows:
        # 0701234567
        # 0771234567
        # +256701234567
        # +256 701 234 567
        cleaned = re.sub(r"[\s-]", "", phone)

        pattern = r"^(?:\+256|0)7\d{8}$"

        if not re.fullmatch(pattern, cleaned):
            raise ValueError(
                "Enter a valid Ugandan phone number "
                "(e.g. 0701234567 or +256701234567)."
            )

        return cleaned

    @staticmethod
    def validate_age(age: str) -> int:
        """Validate worker age."""

        try:
            value = int(age)
        except ValueError as error:
            # Review: Preserve the original exception when reporting invalid age input.
            raise ValueError("Age must be a whole number.") from error

        if value < 1 or value > 100:
            raise ValueError("Age must be between 1 and 100.")

        return value


# ============================================================
# WORKER REGISTRY
# ============================================================

class WorkerRegistry:

    def __init__(self, storage_file: str = "workers.json"):
        self.workers: list[Worker] = []
        self.storage_file = Path(storage_file)

        self.load_data()

    # --------------------------------------------------------
    # ID MANAGEMENT
    # --------------------------------------------------------

    def generate_id(self) -> int:
        """Generate the next unique worker ID."""

        if not self.workers:
            return 1

        return max(worker.worker_id for worker in self.workers) + 1

    # --------------------------------------------------------
    # ADD WORKER
    # --------------------------------------------------------

    def add_worker(
        self,
        name: str,
        address: str,
        phone: str,
        age: str,
    ) -> Worker:

        name = Validator.validate_name(name)
        address = Validator.validate_address(address)
        phone = Validator.validate_phone(phone)
        age_value = Validator.validate_age(age)

        # Prevent duplicate phone numbers
        if self.find_by_phone(phone):
            raise ValueError(
                "A worker with this phone number already exists."
            )

        worker = Worker(
            worker_id=self.generate_id(),
            name=name,
            address=address,
            phone=phone,
            age=age_value,
        )

        self.workers.append(worker)
        self.save_data()

        return worker

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    def find_by_id(self, worker_id: int) -> Optional[Worker]:
        """Find worker using their ID."""

        return next(
            (
                worker
                for worker in self.workers
                if worker.worker_id == worker_id
            ),
            None,
        )

    def find_by_phone(self, phone: str) -> Optional[Worker]:
        """Find worker by phone number."""

        return next(
            (
                worker
                for worker in self.workers
                if worker.phone == phone
            ),
            None,
        )

    def search(self, keyword: str) -> list[Worker]:
        """Search workers by name, address, phone or department."""

        keyword = keyword.lower().strip()

        # Review: Consider rejecting blank keywords because an empty string matches every worker.

        return [
            worker
            for worker in self.workers
            if (
                keyword in worker.name.lower()
                or keyword in worker.address.lower()
                or keyword in worker.phone.lower()
                or keyword in worker.department.value.lower()
            )
        ]

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    def remove_worker(self, worker_id: int) -> bool:
        """Remove a worker by ID."""

        worker = self.find_by_id(worker_id)

        if worker is None:
            return False

        self.workers.remove(worker)
        self.save_data()

        return True

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update_worker(
        self,
        worker_id: int,
        name: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        age: Optional[str] = None,
    ) -> bool:

        worker = self.find_by_id(worker_id)

        if worker is None:
            return False

        if name:
            name = Validator.validate_name(name)

        if address:
            address = Validator.validate_address(address)

        if phone:
            phone = Validator.validate_phone(phone)

            existing = self.find_by_phone(phone)

            if existing and existing.worker_id != worker_id:
                raise ValueError(
                    "Another worker already uses this phone number."
                )

        age_value = None

        if age:
            age_value = Validator.validate_age(age)

        worker.update(
            name=name,
            address=address,
            phone=phone,
            age=age_value,
        )

        self.save_data()

        return True

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    def workers_by_department(
        self,
        department: Department,
    ) -> list[Worker]:

        return [
            worker
            for worker in self.workers
            if worker.department == department
        ]

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    def statistics(self) -> dict:

        total = len(self.workers)

        eligible = sum(
            worker.eligible for worker in self.workers
        )

        not_eligible = total - eligible

        department_counts = {
            department.value: len(
                self.workers_by_department(department)
            )
            for department in Department
        }

        average_age = (
            sum(worker.age for worker in self.workers) / total
            if total
            else 0
        )

        return {
            "total": total,
            "eligible": eligible,
            "not_eligible": not_eligible,
            "average_age": round(average_age, 2),
            "departments": department_counts,
        }

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    def display_all(self) -> None:

        if not self.workers:
            print("\nNo workers registered.")
            return

        print("\n" + "=" * 60)
        print("              WORKER REGISTRY")
        print("=" * 60)

        for worker in self.workers:
            worker.display()

    def display_statistics(self) -> None:

        stats = self.statistics()

        print("\n" + "=" * 60)
        print("              REGISTRY STATISTICS")
        print("=" * 60)

        print(f"Total Workers       : {stats['total']}")
        print(f"Eligible Workers    : {stats['eligible']}")
        print(f"Not Eligible        : {stats['not_eligible']}")
        print(f"Average Age         : {stats['average_age']}")

        print("\nDepartment Breakdown:")

        for department, count in stats["departments"].items():
            print(f"  {department:<30} : {count}")

    # --------------------------------------------------------
    # SAVE DATA
    # --------------------------------------------------------

    def save_data(self) -> None:
        """Save workers to a JSON file."""

        # Review: Reuse Worker.to_dict() here to avoid duplicating serialization logic.
        data = [
            {
                "worker_id": worker.worker_id,
                "name": worker.name,
                "address": worker.address,
                "phone": worker.phone,
                "age": worker.age,
            }
            for worker in self.workers
        ]

        try:
            with self.storage_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

        except OSError as error:
            # Review: Consider an atomic temporary-file replacement to reduce data-loss risk.
            print(f"Warning: Could not save data: {error}")

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    def load_data(self) -> None:
        """Load previously saved workers."""

        if not self.storage_file.exists():
            return

        try:
            with self.storage_file.open("r", encoding="utf-8") as file:
                data = json.load(file)

            # Review: Validate the JSON structure and field types before creating Worker objects.
            # Review: Apply the same validation rules used during registration to loaded records.
            self.workers = [
                Worker(
                    worker_id=item["worker_id"],
                    name=item["name"],
                    address=item["address"],
                    phone=item["phone"],
                    age=item["age"],
                )
                for item in data
            ]

        except (OSError, json.JSONDecodeError, KeyError) as error:
            print(f"Warning: Could not load worker data: {error}")


# ============================================================
# USER INTERFACE
# ============================================================

class WorkerApplication:

    def __init__(self):
        self.registry = WorkerRegistry()

    # --------------------------------------------------------
    # INPUT HELPERS
    # --------------------------------------------------------

    @staticmethod
    def input_worker_details() -> tuple[str, str, str, str]:

        name = input("Enter worker name: ")
        address = input("Enter address: ")
        phone = input("Enter phone number: ")
        age = input("Enter age: ")

        return name, address, phone, age

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    def register_worker(self):

        print("\n=== REGISTER NEW WORKER ===")

        # Review: Add an explicit -> None return annotation to clarify this method's contract.

        try:
            details = self.input_worker_details()

            worker = self.registry.add_worker(*details)

            print("\nWorker registered successfully.")
            worker.display()

        except ValueError as error:
            print(f"\nRegistration failed: {error}")

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    def search_worker(self):

        keyword = input("\nEnter search keyword: ").strip()

        results = self.registry.search(keyword)

        if not results:
            print("\nNo matching workers found.")
            return

        print(f"\nFound {len(results)} worker(s).")

        for worker in results:
            worker.display()

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    def delete_worker(self):

        try:
            worker_id = int(
                input("\nEnter worker ID to delete: ")
            )

            worker = self.registry.find_by_id(worker_id)

            if not worker:
                print("\nWorker not found.")
                return

            worker.display()

            confirmation = input(
                "Are you sure you want to delete this worker? (y/n): "
            ).lower()

            if confirmation == "y":

                self.registry.remove_worker(worker_id)

                print("\nWorker deleted successfully.")

            else:
                print("\nDeletion cancelled.")

        except ValueError:
            print("\nInvalid worker ID.")

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------

    def run(self):

        while True:

            print("\n")
            print("=" * 60)
            print("             WORKER MANAGEMENT SYSTEM")
            print("=" * 60)

            print("1. Register Worker")
            print("2. View All Workers")
            print("3. Search Workers")
            print("4. View Statistics")
            print("5. Delete Worker")
            print("6. Exit")

            choice = input("\nSelect an option: ").strip()

            if choice == "1":
                self.register_worker()

            elif choice == "2":
                self.registry.display_all()

            elif choice == "3":
                self.search_worker()

            elif choice == "4":
                self.registry.display_statistics()

            elif choice == "5":
                self.delete_worker()

            elif choice == "6":
                print("\nThank you for using the Worker Management System.")
                break

            else:
                print("\nInvalid option. Please choose 1–6.")


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():
    """Application entry point."""

    application = WorkerApplication()
    application.run()


if __name__ == "__main__":
    main()