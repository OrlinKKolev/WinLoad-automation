"""Legacy compatibility wrapper. Use app.pipeline.process_schemes instead."""

from app.pipeline.process_schemes import main


if __name__ == "__main__":
    main()