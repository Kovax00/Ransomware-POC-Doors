import ctypes

_user32 = ctypes.windll.user32

GA_ROOT = 2
GWL_STYLE = -16
WS_SYSMENU = 0x00080000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020


def hide_control_box(widget):
    try:
        widget.update_idletasks()
        hwnd = _user32.GetAncestor(int(widget.winfo_id()), GA_ROOT) or int(widget.winfo_id())
        style = _user32.GetWindowLongW(hwnd, GWL_STYLE)
        _user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_SYSMENU)
        _user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                             SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
    except Exception:
        pass
