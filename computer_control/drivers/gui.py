import pyautogui, time
def press(keys): time.sleep(0.1); pyautogui.hotkey(*keys) if isinstance(keys,list) else pyautogui.press(keys)
def click(x=None,y=None): time.sleep(0.1); pyautogui.click(x or pyautogui.position()[0], y or pyautogui.position()[1])
def write(txt): time.sleep(0.1); pyautogui.typewrite(txt,interval=0.03)
