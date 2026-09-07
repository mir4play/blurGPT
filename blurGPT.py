# ==========================
# BlurGPT
# ==========================
# Author: Adler Nicolau
# Date: 21/07/2026
#
# Legacy command-line entry point.
# Processing is delegated to the same BatchProcessor used by the GUI.
# ==========================

from datetime import datetime, timezone

import torch

from core.processor import BatchProcessor



def _print_status(message):
    print(message)



def main():
    print("blurGPT............. command-line mode")
    print(f"PyTorch............. {torch.__version__}")

    if not torch.cuda.is_available():
        print("GPU................. CPU")
        raise RuntimeError(
            "CUDA is not available.\n"
            "Read README.md to install the CUDA version of PyTorch."
        )

    print(f"GPU................. {torch.cuda.get_device_name(0)}")
    print()
    print("Using persistent BlurGPT settings from config/settings.json.")
    print("The CLI and GUI now share the same BatchProcessor and processing configuration.")
    print()

    from core.jobmanager import JobManager

    manager = JobManager()
    processor = BatchProcessor(manager, status_callback=_print_status)

    try:
        result = processor.run()
    except KeyboardInterrupt:
        print()
        print("Cancellation requested — stopping safely...")
        processor.request_cancel()
        result = processor.run()

    print()
    print("Batch processing finished.")
    print(f"Succeeded...........: {result['succeeded']}")
    print(f"Failed..............: {result['failed']}")
    print(f"Cancelled...........: {result['cancelled']}")
    print("Benchmark log.......: logs/benchmarks.jsonl")
    print(f"Run id..............: {processor.run_id}")


if __name__ == "__main__":
    main()
