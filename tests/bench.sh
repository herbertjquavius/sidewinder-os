# Runs inside the VM: task switching speed, then how late a 1 ms timer fires while every CPU is busy
exec > /dev/ttyS0 2>&1
sleep 45
echo "BENCH kernel=$(uname -r) scx=$(cat /sys/kernel/sched_ext/state 2>/dev/null)/$(cat /sys/kernel/sched_ext/root/ops 2>/dev/null)"
for i in 1 2 3 4 5; do
    echo "BENCH hackbench $(perf bench sched messaging -g 8 -l 1000 2>/dev/null | awk '/Total time/{print $3}')"
done
stress-ng --cpu 0 --timeout 70s >/dev/null 2>&1 &
sleep 5
# Normal priority, like a game: ask to wake in 1 ms, measure how late it really wakes
python3 - <<'EOF'
import statistics
import time
late = []
end = time.monotonic() + 60
while time.monotonic() < end:
    t = time.perf_counter_ns()
    time.sleep(0.001)
    late.append((time.perf_counter_ns() - t) / 1000 - 1000)
late.sort()
p99 = late[int(len(late) * 0.99)]
print(f"BENCH cyclic Min: {int(late[0])} Avg: {int(statistics.mean(late))} P99: {int(p99)} Max: {int(late[-1])}")
EOF
wait
echo "BENCH done"
systemctl poweroff
