import time
from app.core.config import settings
from app.services.kafka.producer import send_log_message
from app.services.simulation.log_generator import build_mock_log


def main() -> None:
    try:
        while True:
            log = build_mock_log()
            send_log_message(log)
            print("sent:", log)
            time.sleep(settings.log_producer_interval_seconds)
    except KeyboardInterrupt:
        print("producer stopped")


if __name__ == "__main__":
    main()
