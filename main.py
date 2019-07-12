from bs4 import BeautifulSoup
from PIL import ImageGrab
from io import BytesIO
import base64
import wx.adv
import wx

TRAY_TOOLTIP = 'Inline image generator'
TRAY_ICON = 'icon.ico'


def clip_image_to_html_inline_image():
    """
    Get a image from the clipboard and return the image as a inline base64 encoded <IMG> tag.
    """
    buffered = BytesIO()
    image = ImageGrab.grabclipboard()
    if image:
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        img_str = img_str.decode("utf-8")
        soup = BeautifulSoup('<div></div>')
        new_tag = soup.new_tag('img', src="data:%s;base64,%s" %
                               ('image/jpeg', img_str))
        return str(new_tag)
    return ''


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
        img_tag = clip_image_to_html_inline_image()
        if img_tag:
            copy_html_to_clipboard(img_tag)

    def on_license_info(self, event):
        pass  # TODO

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class App(wx.App):
    def OnInit(self):
        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
