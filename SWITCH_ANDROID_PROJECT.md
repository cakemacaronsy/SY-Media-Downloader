# Bricked Nintendo Switch → Android (Handoff README)

Written 2026-10-04. Purpose: let Claude (or anyone) resume this project without re-asking everything.

> Note: this file lives in the SY-Media-Downloader repo only as a placeholder.
> The owner wants a **fresh start**. The repo-cleanup decision is still open (see "Open decisions").
> Nothing has been deleted, committed or pushed.

## TL;DR
- Goal: revive a bricked Nintendo Switch as something useful.
- **Steam Deck: not feasible.** Switch = ARM (Tegra X1); SteamOS = x86 only. Linux (L4T Ubuntu) runs, but Steam games would need x86 emulation (FEX/Box64): expected to be slow, unverified.
- **Android: feasible.** Switchroot ships **Android 14 (LineageOS 21)** and **Android 15 (LineageOS 22.2)**, Tablet and Android TV variants, for all models (V1/V2/Lite/OLED).
- Whether it works depends on **what "bricked" means** and **which model**. Neither is known yet.

## Known facts (from web search, 2026-10-04; official LineageOS wiki was blocked, so not read first-hand)
- Switchroot Android 14/15 are upstream LineageOS 21 / 22.2. Install follows the official LineageOS wiki: device `nx` (Android TV) and `nx_tab` (Tablet).
- Supports SD card or internal storage install.
- Hekate **v6.1.0+** required.
- Access to RCM:
  - Unpatched V1 (early serials): jig/paperclip + USB-C, no soldering.
  - Patched V1, V2 (Mariko), Lite, OLED: soldered modchip (Picofly, HWFLY, etc.).
- Hard bricks (no power, no RCM, dead eMMC/PMIC, liquid damage) need board-level repair first. Android cannot fix these.
- Soft bricks (boot loop, corrupted OS) are often recoverable; if RCM works, Android can boot from SD even with a dead internal OS.

## Unknowns (ask the user first)
1. Model: V1 (original), V2 (red box), Lite, or OLED?
2. Serial number prefix (e.g. XAW1, XKW1, XAW4, XAJ, XTJ…) → exploitable or patched?
3. Symptoms: black screen, boot loop, stuck logo, no charge, error code, liquid damage?
4. Has the user soldered before / willing to install a modchip?
5. Do they own a PC, USB-C data cable, and a fast microSD (128 GB+)?
6. Use case: tablet, Android TV/console-style, retro gaming, or streaming?

## Decision tree
1. Does it power on / show anything? No → board repair (battery, charge port, PMIC) before anything else.
2. Can it enter RCM (Vol+ and power, with jig inserted; screen stays black, PC detects APX device)?
   - Yes → go to step 4.
   - No → check serial: patched or Mariko → modchip; unpatched V1 → check jig/joy-con rail.
3. Modchip install: soldering required; follow ConsoleMods guides. Decide the chip based on model.
4. Prepare SD card with latest Hekate, partition via Hekate for Android, flash the Switchroot LineageOS build (Tablet or TV variant).
5. Boot, verify Wi-Fi, Bluetooth, Joy-Con, touch, charging, sleep.

## Equipment checklist
- [ ] PC + USB-C **data** cable
- [ ] microSD 128 GB+ (fast, genuine brand)
- [ ] RCM jig (unpatched V1) **or** modchip + soldering gear (everything else)
- [ ] Latest Hekate (≥ 6.1.0)
- [ ] Switchroot / LineageOS `nx` or `nx_tab` build and its guide
- [ ] Optional: backup of existing NAND/keys if the console still partly boots (do this BEFORE changing anything)

## Things not yet verified
- Stability of Android 14/15 builds (Joy-Con, GPU performance, sleep, known issues).
- Official install steps, since the LineageOS wiki was unreachable from the cloud sandbox. Read them directly before acting.
- Switch 2: no information found; assumed irrelevant to a Switch 1 console.

## Sources
- Switchroot wiki, Android 14/15: https://wiki.switchroot.org/wiki/android/android-14-15
- Switchroot wiki, Android: https://wiki.switchroot.org/wiki/android
- LineageOS wiki, nx install: https://wiki.lineageos.org/devices/nx/install/variant3/ and https://wiki.lineageos.org/devices/nx/install/variant4/
- ConsoleMods, RCM: https://consolemods.org/wiki/Rcm
- ConsoleMods, modchips: https://consolemods.org/wiki/Switch:Modchips

## Open decisions
- **Repo handling** (owner has not answered): (a) wipe local files only, (b) delete the GitHub repo `cakemacaronsy/sy-media-downloader` (permanent), or (c) create a new empty repo for this project. Claude recommended (c). Do not delete anything without explicit confirmation.

## How to resume (prompt for next session)
> Read `SWITCH_ANDROID_PROJECT.md`. Here are my answers: model = ___, serial = ___, symptoms = ___, willing to solder = ___. Re-check the Switchroot Android 14/15 and LineageOS `nx` wiki for current instructions, then give me a step-by-step plan.
