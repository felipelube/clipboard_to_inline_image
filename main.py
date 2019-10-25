from bs4 import BeautifulSoup
from PIL import ImageGrab
from io import BytesIO
import wx.lib.newevent
import win32clipboard
import win32api
import win32gui
import win32con
import base64
import wx.adv
import wx

TRAY_TOOLTIP = 'Inline image generator'
TRAY_ICON = 'icon.ico'


def reinsert_dib_format():
    """
    If the clipboard contains data of a imagem in CF_DIBV5 format, reinsert it into the clipboard,
    automatically alongside with a CF_DIB version.
    This solves a issue where the MS Outlook does not populate the CF_DIB format, only the CF_DIBV5
    causing ImageGrab.grabclipboard() to not recognize the image.
    TODO: deal with a error state e.g. cannot open the clipboard.
    """
    try:
        win32clipboard.OpenClipboard()
        hwndDC = win32clipboard.GetClipboardData(
            win32clipboard.CF_DIBV5)
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIBV5, hwndDC)
    except TypeError:
        pass  # there is no CF_DIBV5 in the clipboard, ignore
    finally:
        win32clipboard.CloseClipboard()


def clip_image_to_html_inline_image(image):
    """
    Get a image from the clipboard and return the image as a inline base64 encoded <IMG> tag.
    """
    if image:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        img_str = img_str.decode("utf-8")
        soup = BeautifulSoup('<div></div>')
        new_tag = soup.new_tag('img', src="data:%s;base64,%s" %
                               ('image/jpeg', img_str))
        return str(new_tag)
    return ''


def grab_image():
    """
    Tries to get the imagem from clipboard using ImageGrab.grabclipboard() and uses
    reinsert_dib_format() if necessary.
    """
    image = ImageGrab.grabclipboard()

    if image:
        img_tag = clip_image_to_html_inline_image(image)
    else:
        reinsert_dib_format()
        img_tag = clip_image_to_html_inline_image(image)

    if img_tag:
        copy_html_to_clipboard(img_tag)


def copy_html_to_clipboard(html):
    """
    Copy the html string into the clipboard as a HTML object.
    """
    if not wx.TheClipboard.IsOpened():
        do = wx.HTMLDataObject()
        do.SetHTML(html)
        wx.TheClipboard.Open()
        res = wx.TheClipboard.SetData(do)
        wx.TheClipboard.Close()
        return res
    return False


def create_menu_item(menu, label, func):
    """
    Small helper to create a menu item.
    """
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Licenças', self.on_license_info)
        menu.AppendSeparator()
        create_menu_item(menu, 'Sair', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        grab_image()

    def on_license_info(self, event):
        pass  # TODO

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class CustomFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)

        # Replace the default WndProc with ours, so we can process messages
        self.oldWndProc = win32gui.SetWindowLong(self.GetHandle(),
                                                 win32con.GWL_WNDPROC,
                                                 self.CustomWndProc)

        # Adds this window to the chain of clipboard viewers, saves the next window in the clipboard
        # viewer chain
        self.hwndNextViewer = win32clipboard.SetClipboardViewer(
            self.GetHandle())

    def onChangeCBChain(self, hWnd, msg, wParam, lParam):
        """
        Deals with the chain of clipboard viewers.
        More info: https://docs.microsoft.com/en-us/windows/win32/dataxchg/wm-changecbchain#remarks
        """
        if wParam == self.hwndNextViewer:
            self.hwndNextViewer = lParam

        elif self.hwndNextViewer:
            win32gui.SendMessage(self.hwndNextViewer, msg, wParam, lParam)

    def CustomWndProc(self, hWnd, msg, wParam, lParam):
        if msg == win32con.WM_DESTROY:
            # Removes the window from the chain of clipboard viewers.
            win32clipboard.ChangeClipboardChain(hWnd, self.hwndNextViewer)
            # Restores the old WndProc when closing the application to give the wx framework
            # opportunity to deal with the messages from the OS.
            win32api.SetWindowLong(hWnd, win32con.GWL_WNDPROC, self.oldWndProc)

        # Processes the clipboard on change
        if msg == win32con.WM_DRAWCLIPBOARD:
            grab_image()

        if msg == win32con.WM_CHANGECBCHAIN:
            self.onChangeCBChain(hWnd, msg, wParam, lParam)

        # Pass all messages on to the original WndProc
        return win32gui.CallWindowProc(self.oldWndProc, hWnd, msg, wParam, lParam)


class App(wx.App):
    def OnInit(self):
        frame = CustomFrame()
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
