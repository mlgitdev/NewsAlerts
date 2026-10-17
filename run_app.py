"""Entry point for NewsAlerts standalone executable and launcher."""
import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from app.main import main
    main()
