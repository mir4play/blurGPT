# ==========================
# BlurGPT
# ==========================
# Author: Adler Nicolau
# Date: 21/07/2026
#
# Command-line entry point.
# Processing is delegated to the same BatchProcessor used by the GUI.
# ==========================

from core.paths import LOGS_DIR
from core.processor import BatchProcessor


def _print_status(message):
    print(message)


def main():
    print("blurGPT............. command-line mode")
    print("Using persistent BlurGPT settings from config/settings.json.")
    print("The CLI and GUI share the same BatchProcessor and processing configuration.")
    print()

    from core.jobmanager import JobManager

    manager = JobManager()
    processor = BatchProcessor(manager, status_callback=_print_status)
    result = processor.run()

    print()
    print("Batch processing finished.")
    print(f"Succeeded...........: {result['succeeded']}")
    print(f"Failed..............: {result['failed']}")
    print(f"Cancelled...........: {result['cancelled']}")
    print(f"Benchmark log.......: {LOGS_DIR / 'benchmarks.jsonl'}")
    print(f"Run id..............: {processor.run_id}")


if __name__ == "__main__":
    main()
