---
title: "Restarting from Windows can break laptop speakers on Linux"
date: 2026-10-23
draft: false
---

Found this after a few hours of blaming PipeWire.

My Zenbook (Realtek ALC294) played sound for 3-4 seconds and then the built-in speakers just went silent. Firefox, mpv,
didn't matter. My USB interface worked fine. `aplay` straight to the hw device died the same way so PipeWire was out.

I wanted a number instead of my ears. A capture stream's `hw_ptr` only moves when the codec actually delivers samples
so recording from the internal mic should add 48000 frames every second:

```bash
arecord -D hw:1,0 -f S16_LE -r 48000 -c 2 -t raw /dev/null &
while sleep 0.5; do grep hw_ptr /proc/asound/card1/pcm0c/sub0/status; done
```

Frames per second, sampled every half second:

```
48003 47733 43137 35461 25801 14559 6013 2652 2063 1839
```

About 1.5 seconds after the codec powered up its clock slid down to ~2 kHz and stayed there. Same curve every run, even
with nothing playing. So the codec itself was dying.

I was sure the kernel update did it. But the sound modules from 7.2.9 and 7.2.11 were byte identical except two new
quirk table entries for other laptops.

What actually did it was clicking Restart in Windows. A restart never cuts power to the codec, so whatever the Windows
Realtek driver left in it was still there when Linux booted and Linux doesn't reset it. Rebooting Linux didn't help. S3
sleep didn't help either. A full shutdown fixed it, the same loop now shows 48000 the whole time.

The kernel already knows the Windows driver does this on some ASUS laptops with the same codec, there are comments about
it leaving coef `0x10` set (`alc294_gx502_toggle_output` in `sound/hda/codecs/realtek/alc269.c`). I haven't found which
register it is on mine yet.

Same thing on other Zenbooks: [Launchpad #1742852](https://bugs.launchpad.net/ubuntu/+source/alsa-driver/+bug/1742852),
[pop-os/pop#949](https://github.com/pop-os/pop/issues/949).

Shut down Windows before going to Linux. Don't restart.
