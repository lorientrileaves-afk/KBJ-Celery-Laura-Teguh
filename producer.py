"""Producer: generates inputs and publishes Celery tasks to an exchange."""
import argparse
import json
import random
import time
from uuid import uuid4

from app.celery_app import app, fanout, topic, wildcard, QUEUES
from app.tasks import process_event

SCENARIOS = {
    "fanout": (fanout, ["sensor.temperature", "system.alert"]),
    "topic": (topic, ["sensor.temperature", "sensor.humidity", "system.warning.disk", "other.misc"]),
    "wildcard": (wildcard, ["sensor.room.critical", "sensor.critical", "sensor.room.floor.critical", "device.other"]),
}


def generate_event(index):
    return {
        "event_id": str(uuid4()),
        "source": "sensor-a" if index % 2 == 0 else "sensor-b",
        "kind": "temperature",
        "value": round(random.uniform(15, 100), 2),
    }


def publish(scenario, count, interval):
    exchange, keys = SCENARIOS[scenario]
    # Queue declarations are included for first-run safety; workers also declare them.
    for index in range(count):
        routing_key = keys[index % len(keys)]
        event = generate_event(index)
        async_result = process_event.apply_async(
            kwargs={"event": event, "scenario": scenario, "routing_key": routing_key},
            exchange=exchange,
            routing_key=routing_key,
            declare=list(QUEUES),
            retry=True,
            retry_policy={"max_retries": 3, "interval_start": 0, "interval_step": 1},
        )
        print(json.dumps({"sent": index + 1, "scenario": scenario,
                          "routing_key": routing_key, "task_id": async_result.id,
                          "event": event}, ensure_ascii=False))
        if interval:
            time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generator pesan untuk RabbitMQ + Celery")
    parser.add_argument("--scenario", choices=[*SCENARIOS, "all"], default="all")
    parser.add_argument("--count", type=int, default=8, help="Jumlah pesan per skenario")
    parser.add_argument("--interval", type=float, default=0.15)
    args = parser.parse_args()
    if args.count < 1 or args.interval < 0:
        parser.error("--count harus >= 1 dan --interval >= 0")
    for scenario in (SCENARIOS if args.scenario == "all" else [args.scenario]):
        publish(scenario, args.count, args.interval)
