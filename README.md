# MIDIMix Magician

##### Easy Peasy AKAI MIDIMix Support For FL Studio

![](https://www.akaipro.com/assets/images/pdp/midi-mix/midimix_ortho_1200x750_web.jpg_c85a5d661225028785319086bc4e547c.jpg)

## The Problem
It's a question as old as time. Ever just wanted to plug in your AKAI MIDIMix and have it work as a mixer with FL Studio only to find it is not officially supported and you spend hours browsing online for scripts and manually linking 50 controls and it still isn't working as well as you had hoped so by the time you wanna work on music you are all burned out and wanna hit the bar 30 minutes before close and see how many beer/shot combos you can dump in your body so you feel numb enough to go home and buy a copy of Abelton Live so you can use your controller in a DAW you are unfamilier with? I know I have.

> Do I look like I know what Python is? I just want a god dang mixer controller. -- Hank Hill

## The Solution

Well now there is an answer. This is a Shutterstock photo of a local magician I found on Craigslist. He said I can convert his whole essence and entrap his soul into a Python script forever so he can do the hard part for us.

![](https://www.shutterstock.com/image-photo/magician-bowler-hat-above-his-260nw-1276255153.jpg)

His name is Ted. And before this he had no meaningful purpose and was looking for any means necessary to get out of his loveless marriage. Thank Ted for his sacrifice. I once saw Ted on a 6 day bender with a lady of the night while ignoring calls and texts from his wife and kids. HE WAS MADE FOR THIS. HE LIKES ROUTING MIDI CC MESSAGES FOR YOU. I DIDN'T TRICK HIM INTO THIS!

## The Real Talk

This project is a fork and partial rewrite of [Akai Midimix Reimagined](https://forum.image-line.com/viewtopic.php?t=266822) by [natraj](https://support.image-line.com/action/profile/public?fu=1068) resleased in 2021. So big credit to him on doing some of the initial groundwork and heavy lifting. But I always thought it felt more of a proof of concept rather than a production script that AKAI would have shipped with. I have done bug fixes, optimizations, and quality of life improvements where it not only simplifies things but it makes it a pretty darn good dedicated controller for FL Studio's mixer.

### Features / Enhancements

- Already mapped out and ready to go control of 64 tracks all broken down to 8 mixer groups of 8 tracks
- Instant control of 3 band Gain EQ, 3 Band Frequency EQ, Panning, and Stereo separation
- Mute, solo, and record arming modes
- Send All to send all hardware settings to your current mixer group
- "Controller mode" from Reimagined was removed but you have 8 CC assignable knobs to anything you want in FL Studio or plugins
- Automatic track focus in FL Studio based off the control you are using
- Reimagines LED bugs are resolved and their on and off states reflect their usage better in Mute/Solo/Arm modes
- Volume ceiling defaults to 0.0 dB but you can expand to +5.6 dB with an easy script change

## Setup

Download device_MIDIMixMagician.py and copy it to
`<Your My Documents Folder>\Image-Line\FL Studio\Settings\Hardware\AKAI MIDIMix`. If  the `AKAI MIDIMix` folder doen't exist just create it.

Open up FL Studio, select `MIDI Mix` under inputs. Go to the dropdown `Controller Type` and select `AKAI MIDIMix Magician (user)`.  Be sure to set `MIDI Mix` under outputs to recieve MIDI information as well so the device can reflect FL's mixer state.

## The UI and Usage

The UI work flow doesn't 100% match the labeling on the AKAI MIDIMix. But is incredibly easy to remember and understand after a quick session.

- The mute buttons will be used for mute, solo, and arm depending what mode you are in
- The rec arm buttons will always be used to change between mixer groups (First one is tracks 1-8, second is 9-16, ect)
- Button "Bank Left" goes into mute mode
	- All the knobs control 3 band Gain EQs over 8 tracks
	- The mute buttons will be yellow if the track is muted
- Button "Bank Right" goes into rec arm mode
	- All the knobs control 3 band Frequency EQs over 8 tracks
	- The mute buttons will be yellow if the track is armed
- Button "Solo" goes into solo mode
	- All mute buttons will light as muted except the track you are soloing
	- The first row of knobs control panning over 8 tracks
	- The second row of knobs control stereo separation over 8 tracks
	- The third row of knobs can be used as linkable MIDI CC knobs
	- The CC numbers from left to right are 70-77 but can be changed in the script
 - Sliders 1-8 control the tracks on the current mixer group and the master slider the master track
