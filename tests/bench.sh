# Runs inside the VM: task switching speed, then wakeup delay while every CPU is busy
exec > /dev/ttyS0 2>&1
sleep 45
echo "BENCH kernel=$(uname -r) scx=$(cat /sys/kernel/sched_ext/state 2>/dev/null)/$(cat /sys/kernel/sched_ext/root/ops 2>/dev/null)"
for i in 1 2 3 4 5; do
    echo "BENCH hackbench $(hackbench -g 8 -l 1000 | awk '/Time/{print $2}')"
done
stress-ng --cpu 0 --timeout 70s >/dev/null 2>&1 &
sleep 5
cyclictest -q -m -t -p0 -i 1000 -D 60 | sed 's/^/BENCH cyclic /'
wait
echo "BENCH done"
systemctl poweroff
