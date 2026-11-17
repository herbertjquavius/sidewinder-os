# Turns the benchmark logs into a small markdown table
import re
import statistics
import sys


def parse(path):
    text = open(path, errors="ignore").read()
    kernel = re.search(r"BENCH kernel=(\S+) scx=(\S*)", text)
    hack = [float(x) for x in re.findall(r"BENCH hackbench ([\d.]+)", text)]
    avgs = [int(x) for x in re.findall(r"BENCH cyclic .*?Avg:\s*(\d+)", text)]
    maxs = [int(x) for x in re.findall(r"BENCH cyclic .*?Max:\s*(\d+)", text)]
    return {
        "kernel": kernel.group(1) if kernel else "?",
        "scx": kernel.group(2) if kernel else "?",
        "hack": statistics.median(hack) if hack else None,
        "avg": statistics.mean(avgs) if avgs else None,
        "max": max(maxs) if maxs else None,
    }


def cell(v, fmt):
    return fmt.format(v) if v is not None else "n/a"


def main(pairs):
    print("| Setup | Kernel | Scheduler | Task switching (s, lower is better) | Avg wakeup delay under load (µs) | Worst wakeup delay (µs) |")
    print("|---|---|---|---|---|---|")
    for name, path in pairs:
        r = parse(path)
        print(f"| {name} | {r['kernel']} | {r['scx'] or 'none'} | {cell(r['hack'], '{:.3f}')} | "
              f"{cell(r['avg'], '{:.0f}')} | {cell(r['max'], '{}')} |")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(list(zip(args[::2], args[1::2])))
