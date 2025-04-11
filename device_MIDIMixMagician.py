# name=AKAI MIDIMix Magician
# version=1.2
# github=https://github.com/baconbrad/MIDIMixMagician

import midi
import device
import mixer
import general
import time
import transport

# Change values to change default behavior
VolCeiling = 0.8    # Maximum volume level for track volume control (0.8: 0.0 dB, 1: +5.6 dB)
MastVolCeiling = 1  # Maximum volume level for master volume control (0.8: 0.0 dB, 1: +5.6 dB)
MIDIPort = 1        # Port to send the customized CC knobs from
ActiveTab = 0       # Active tab (0: EQ Gain/Mute, 1: EQ Freq/Arm 2: Pan and CC/Solo)
MixerPage = 0       # Default mixer page (0: Tracks 1-8, 1: Tracks 9-16, etc)
Debug = True        # Print to script output

# Don't touch anything below unless you know what you are doing

# States and global information
btnMute = False     # Button Bank Left state
btnArm = False      # Button Bank Right state
btnSolo = False     # Button Solo state
blinkState = False  # Current state of blinking LEDs
lastBlink = 0       # Timestamp of last blink       
blinkInt = 0.5      # Blink interval for idle state
BTN_MUTE = 0x19     # MIDI note for Bank Left
BTN_ARM = 0x1A      # MIDI note for Bank Right
BTN_SOLO = 0x1B     # MIDI note for Solo
KNOBS = [0x12,      # MIDI for last row of knobs in solo mode
        0x16,
        0x1a,
        0x1e,
        0x30,
        0x34,
        0x38,
        0x3c]

# MIDI Control Change (CC) mappings
CCs = [16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61]
KnobCCs = [70,71,72,73,74,75,76,77] 

def channel2note(channel):
    """
    Converts a track/channel number to a corresponding MIDI note number.

    Args:
    channel (int): Track/channel number (1–16).

    Returns:
    int: Corresponding MIDI note number.
    """
    switcher = {1:1, 2:4, 3:7, 4:10, 5:13, 6:16, 7:19, 8:22, 9:3, 10:6, 11:9, 12:12, 13:15, 14:18, 15:21, 16:24}
    return switcher.get(channel, 0)

def note2channel(note):
    """
    Converts a MIDI note number to a corresponding track/channel number.

    Args:
    note (int): MIDI note number.

    Returns:
    int: Corresponding track/channel number (1–16).
    """
    switcher = {1:1, 4:2, 7:3, 10:4, 13:5, 16:6, 19:7, 22:8, 3:9, 6:10, 9:11, 12:12, 15:13, 18:14, 21:15, 24:16}
    return switcher.get(note, 0)

def mixerSetChannelValue(chan, recevent, value):
    """
    Updates a track's mixer channel value (e.g., volume, pan, EQ).

    Args:
    chan (int): Track/channel number.
    recevent (int): The specific mixer event (e.g., volume, pan).
    value (float): The value to set, typically normalized between 0 and 1.
    """
    general.processRECEvent(recevent + mixer.getTrackPluginId(chan, 2), round(value), midi.REC_UpdateControl | midi.REC_UpdateValue | midi.REC_ShowHint)

def setMixerEQGain(chan, band, value):
    """
    Set the gain of a specific EQ band on a track.

    Args:
    chan (int): Track/channel number.
    band (int): EQ band number (0–2).
    value (float): Gain value for the band, between -1 and 1.
    """
    general.processRECEvent(midi.REC_Mixer_EQ_Gain+band+mixer.getTrackPluginId(chan, 0), round(value*1800), midi.REC_UpdateControl | midi.REC_UpdateValue | midi.REC_ShowHint)    

def setMixerEQFrequency(chan, band, value):
    """
    Set the frequency of a specific EQ band on a track.

    Args:
    chan (int): Track/channel number.
    band (int): EQ band number (0–2).
    value (float): Frequency value, between 0 and 1.
    """
    general.processRECEvent(midi.REC_Mixer_EQ_Freq+band+mixer.getTrackPluginId(chan, 0), round(value*65535), midi.REC_UpdateControl | midi.REC_UpdateValue | midi.REC_ShowHint)  

def setMixerEQQ(chan, band, value):
    """
    Set the Q (resonance) of a specific EQ band on a track.

    Args:
    chan (int): Track/channel number.
    band (int): EQ band number (0–2).
    value (float): Q value, between 0 and 1.
    """
    general.processRECEvent(midi.REC_Mixer_EQ_Q+band+mixer.getTrackPluginId(chan, 0), round(value*65535), midi.REC_UpdateControl | midi.REC_UpdateValue | midi.REC_ShowHint)  

def LED_On(led):
    """
    Turn on an LED.

    Args:
    led (int): The MIDI note corresponding to the LED.
    """
    device.midiOutMsg(0x90, 0, led, 0x7F)
    device.midiOutMsg(0x80, 0, led, 0x7F)

def LED_Off(led):
    """
    Turn off an LED.

    Args:
    led (int): The MIDI note corresponding to the LED.
    """
    device.midiOutMsg(0x90, 0, led, 0)
    device.midiOutMsg(0x80, 0, led, 0)

def updateLED(led, state):
    """
    Update the state of an LED (on/off).

    Args:
    led (int): The MIDI note corresponding to the LED.
    state (bool): True to turn the LED on, False to turn it off.
    """
    if state:
        LED_On(led)
    else:
        LED_Off(led)

def setActiveTab(tab):
    """
    Set the active tab (Mute/Solo/Arm) and update LED states accordingly.

    Args:
    tab (int): The tab to set as active (0: Mute, 1: Solo, 2: Arm).
    """
    global ActiveTab
    ActiveTab = tab
    tab_leds = {
        0: BTN_MUTE,
        1: BTN_ARM,
        2: BTN_SOLO
    }

    # Update LED states based on active tab
    for tab_key, led in tab_leds.items():
        updateLED(led, tab == tab_key)

    setMixerPage(MixerPage)

def setMixerPage(mp):
    """
    Set the mixer page and update track LEDs based on track state (mute, solo, arm).

    Args:
    mp (int): The mixer page to display (0–n).
    """
    global MixerPage
    MixerPage = mp
    for a in range(1,9):
        if ActiveTab==0:
            if (mixer.isTrackMuted(a+(MixerPage*8))): 
                LED_Off( channel2note(a) )     
            else: 
                LED_On( channel2note(a) )
        if ActiveTab==1:
            if (mixer.isTrackArmed(a+(MixerPage*8))): 
                LED_On( channel2note(a) )     
            else: 
                LED_Off( channel2note(a) )
        if ActiveTab==2:
            if (mixer.isTrackSolo(a+(MixerPage*8))): 
                LED_Off( channel2note(a) )     
            else: 
                LED_On( channel2note(a) )
    for a in range(1,9):
        if (a-1)==MixerPage: 
            LED_On( channel2note(a+8) )
        else: 
            LED_Off( channel2note(a+8) )

def toggleProps(a):
    """
    Toggle the properties (mute, solo, arm) of a track.

    Args:
    a (int): The track/channel number.
    """
    global MixerPage
    track = a+(MixerPage*8)
    if ActiveTab==0:
        mixer.muteTrack(track)
        if mixer.isTrackMuted(track): 
            LED_Off( channel2note(a) )
        else: 
            LED_On( channel2note(a) )
    if ActiveTab==1:
        mixer.armTrack(track)
        if mixer.isTrackArmed(track): 
            LED_Off( channel2note(a) )
        else: 
            LED_On( channel2note(a) )
    if ActiveTab==2:
        mixer.soloTrack(track)
        for a in range(1,9):
            if (mixer.isTrackMuted(a+(MixerPage*8))): 
                LED_Off( channel2note(a) )     
            else: 
                LED_On( channel2note(a) )

def OnIdle():
    """
    OnIdle function tracking the blinking LEDs for arm mode
    """
    global blinkState, lastBlink

    if ActiveTab == 1:
        if transport.isPlaying():
            # Show solid lights while playing
            for a in range(1, 9):
                track = a + (MixerPage * 8)
                if mixer.isTrackArmed(track):
                    LED_On(channel2note(a))
                else:
                    LED_Off(channel2note(a))
        else:
            # Blink armed tracks while not playing
            currentBlink = time.time()
            if currentBlink - lastBlink >= blinkInt:
                blinkState = not blinkState
                lastBlink = currentBlink

                for a in range(1, 9):
                    track = a + (MixerPage * 8)
                    if mixer.isTrackArmed(track):
                        if blinkState:
                            LED_On(channel2note(a))
                        else:
                            LED_Off(channel2note(a))               

def OnInit():
    """
    Initialization function to set up the MIDI mixer's page and active tab.
    """
    global MidimixPort
    global MixerPage
    setMixerPage(MixerPage)
    setActiveTab(ActiveTab)
    
def OnDeInit():
    """
    De-initialization function to turn off all LEDs on the controller.
    """
    LED_Off(BTN_MUTE)
    LED_Off(BTN_ARM)
    LED_Off(BTN_SOLO)
    for i in range(1, 17):
        LED_Off(channel2note(i))
        
def handleMixerControlChange(chan, row, event_data2):
    """
    Handle different mixer control changes (volume, pan, stereo separation, EQ).
    
    Args:
    chan (int): Track/channel number.
    row (int): The row in the control matrix (0: pan, 1: stereo sep, etc.).
    event_data2 (int): The value of the control change (0–127).
    """
    if ActiveTab == 0:  # EQ controls
        if row == 0:  # EQ Gain (Band 2)
            setMixerEQGain(chan, 2, (2 * event_data2 / 127) - 1)
        elif row == 1:  # EQ Gain (Band 1)
            setMixerEQGain(chan, 1, (2 * event_data2 / 127) - 1)
        elif row == 2:  # EQ Gain (Band 0)
            setMixerEQGain(chan, 0, (2 * event_data2 / 127) - 1)
        elif row == 3:  # Volume
            mixer.setTrackVolume(chan, VolCeiling * event_data2 / 127)
    
    elif ActiveTab == 1:  # EQ Frequency controls
        if row == 0:  # EQ Frequency (Band 2)
            setMixerEQFrequency(chan, 2, event_data2 / 127)
        elif row == 1:  # EQ Frequency (Band 1)
            setMixerEQFrequency(chan, 1, event_data2 / 127)
        elif row == 2:  # EQ Frequency (Band 0)
            setMixerEQFrequency(chan, 0, event_data2 / 127)
        elif row == 3:  # Volume
            mixer.setTrackVolume(chan, VolCeiling * event_data2 / 127)

    elif ActiveTab == 2:  # Standard mixer controls
        if row == 0:  # Pan
            mixer.setTrackPan(chan, (2 * event_data2 / 127) - 1)
        elif row == 1: # Stereo Separation
            mixer.setTrackStereoSep(chan, (2 * event_data2 / 127) - 1)
        elif row == 2: # Linkable Knob
            return  # Let FL Studio handle it
        elif row == 3:  # Volume
            mixer.setTrackVolume(chan, VolCeiling * event_data2 / 127)

def OnMidiMsg(event):
    """
    Handle incoming MIDI messages (Note On, Note Off, Control Change).
    
    Args:
    event (MIDIEvent): The MIDI event to process.
    """
    global btnMute
    global btnArm
    global btnSolo
    if event.midiId == midi.MIDI_NOTEON:
        if Debug == True:
            print('Note On: ' + 'Status (' + hex(event.status) + ') ' + 'Data 1 (' + hex(event.data1) + ') Data 2 (' + hex(event.data2) + ')')        
        if event.data1 == BTN_MUTE: 
            btnMute = True
        elif event.data1 == BTN_ARM: 
            btnArm = True
        elif event.data1 == BTN_SOLO: 
            btnSolo = True
        else:
            ch = note2channel(event.data1)
            if ch < 9: toggleProps(ch)
            else: setMixerPage(ch-9)
        event.handled = True

    if event.midiId == midi.MIDI_NOTEOFF:
        if Debug == True:
            print('Note Off: ' + 'Status (' + hex(event.status) + ') ' + 'Data 1 (' + hex(event.data1) + ') Data 2 (' + hex(event.data2) + ')')     
        if event.data1 == BTN_MUTE: 
            setActiveTab(0)
            btnMute = False
        elif event.data1 == BTN_ARM: 
            setActiveTab(1)
            btnArm = False
        elif event.data1 == BTN_SOLO: 
            setActiveTab(2)
            btnSolo = False
        else:
            setActiveTab(ActiveTab) # Temp fix for weird LED behavior     
        event.handled = True

    if event.midiId == midi.MIDI_CONTROLCHANGE:
        if Debug:
            print('CC: ' + 'Status (' + hex(event.status) + ') ' + 'Data 1 (' + hex(event.data1) + ') Data 2 (' + hex(event.data2) + ')')
        if event.data1 in KNOBS:  # Ensure event.data1 is in KNOBS list
            idx = KNOBS.index(event.data1)
            if idx < len(KnobCCs):
                knob_cc = KnobCCs[idx]  
                # Send Control Change (CC) message to FL Studio
                device.midiOutMsg(0xB0, MIDIPort, knob_cc, event.data2)
                if Debug:
                    print('Knob: Index (' + str(idx) + ') CC (' + str(knob_cc) + ')')
                
        # Handle other CC events (non-knob)
        else:
            if event.data1 == 62:
                mixer.setTrackNumber(0)
                mixer.setTrackVolume(0, MastVolCeiling * event.data2/127)
            elif event.data1 in CCs:
                idx = CCs.index(event.data1)
                row = idx % 4
                col = idx // 4
                chan = (col + 1) + (8 * MixerPage)
                mixer.setTrackNumber(chan)
                handleMixerControlChange(chan, row, event.data2)
            else:
                if Debug:
                    print('Unknown CC: ' + hex(event.data1))
        
        event.handled = True
    
    return
