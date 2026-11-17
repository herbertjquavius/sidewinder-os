| Setup | Kernel | Scheduler | Task switching (s, lower is better) | Avg wakeup delay under load (µs) | 99% of wakeups within (µs) | Worst wakeup delay (µs) |
|---|---|---|---|---|---|---|
| Stock Fedora | 7.3.3-300.fc45.x86_64 | disabled/ | 3.971 | 84 | 119 | 38019 |
| CachyOS kernel | 7.3.4-1.cachyos1.fc45.x86_64 | disabled/ | 4.451 | 75 | 105 | 1080 |
| CachyOS + LAVD | 7.3.4-1.cachyos1.fc45.x86_64 | enabled/lavd_1.1.4_x86_64_unknown_linux_gnu | 4.301 | 79 | 104 | 9684 |
