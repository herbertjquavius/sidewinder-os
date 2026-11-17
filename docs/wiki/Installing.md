# Installing

> ⚠️ **Installing erases the whole drive.** Every file, game and save on that computer is gone. Back up first.

## 1. Back up your saves
- Most Steam games keep saves in Steam Cloud. Check: in Steam, right-click a game, then **Properties**, then **General**, and look for **Steam Cloud**.
- For games without cloud saves, copy their save folders to a USB drive or cloud storage. Search "<game name> save location" if you're not sure where they are.

## 2. Make the USB stick
You need a USB stick of 8 GB or bigger. It gets erased too.
1. On any computer, download the Sidewinder ISO file.
2. Install **Fedora Media Writer** or **balenaEtcher** (both free).
3. Open it, pick the Sidewinder ISO, pick the USB stick, and write it.

## 3. Boot from the USB stick
1. Plug the stick into the computer that's getting Sidewinder.
2. Turn it on and tap the boot menu key right away. It's usually **F12**, **F11**, **F9**, **F8** or **Esc**. The brand logo screen often says which.
3. Pick the USB stick from the list.

## 4. Install
1. Pick your language.
2. Pick the drive to install to. It will be erased.
3. Start the install and wait. It takes 5 to 15 minutes.
4. Restart and pull out the USB stick when it says so.

## 5. The blue screen (only once)
If Secure Boot is on, the first restart shows a blue screen called **MOK management**. This lets the computer trust Sidewinder.
1. Pick **Enroll MOK**, then **Continue**, then **Yes**.
2. Type the password `sidewinder` (nothing shows while you type, that's normal) and press Enter.
3. Pick **Reboot**.

Then go to [[First boot]].
