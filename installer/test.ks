
# Test copy only: erases the first VM disk without asking and shows the boot menu
ignoredisk --only-use=vda
zerombr
clearpart --all --initlabel --disklabel=gpt
autopart --noswap

%post
for B in /boot /sysroot/boot; do
    if [ -f "$B/grub2/grubenv" ]; then
        grub2-editenv "$B/grub2/grubenv" unset menu_auto_hide || true
        break
    fi
done
true
%end
