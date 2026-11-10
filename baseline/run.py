import time

from agents.data.agent import process_dataset
from agents.training.agent import run_training


def run_baseline() -> dict:
    t0 = time.time()
    state = process_dataset()
    state.update(run_training(state))
    state["duration_s"] = round(time.time() - t0, 2)
    return state


if __name__ == "__main__":
    print(run_baseline())