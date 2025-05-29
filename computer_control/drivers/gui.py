import pyautogui, time, platform, pyperclip

def _pause(): time.sleep(0.05)

def press(keys):
    _pause()
    pyautogui.hotkey(*keys) if isinstance(keys,list) else pyautogui.press(keys)

def click(x=None,y=None):
    _pause(); pyautogui.click(x or pyautogui.position()[0], y or pyautogui.position()[1])

def move(x,y): _pause(); pyautogui.moveTo(x,y,duration=0.15)

def drag(x1,y1,x2,y2,duration=0.2):
    _pause(); pyautogui.moveTo(x1,y1); pyautogui.dragTo(x2,y2,duration)

def scroll(amount): _pause(); pyautogui.scroll(amount)

def write(text):
    _pause()
    if len(text)>50:
        pyperclip.copy(text)
        mod='command' if platform.system()=="Darwin" else 'ctrl'
        pyautogui.hotkey(mod,'v')
    else:
        pyautogui.typewrite(text,interval=0.02)
