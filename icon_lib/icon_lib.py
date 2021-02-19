import os
import warnings
import ctypes
from ctypes import POINTER, Structure, c_wchar, c_int, sizeof, byref
from ctypes.wintypes import BYTE, WORD, DWORD, LPWSTR, LPSTR
import win32api    


class SetFolderIcon(object):
    def __init__(self, folderPath, iconPath, set_file_name_only=False, reset=False):
        assert os.path.isdir(folderPath), "folderPath '%s' is not a valid folder"%folderPath
        self.__folderPath = os.path.abspath(folderPath)
        assert os.path.isfile(iconPath), "iconPath '%s' does not exist"%iconPath
        self.__iconPath = os.path.abspath(iconPath)
        assert isinstance(reset, bool), "reset must be boolean"
        self.__reset = reset
        self.__set_file_name_only = set_file_name_only
        

        ini_path = folderPath + "\\" + "desktop.ini"
        if (os.path.isfile(ini_path)):
            os.remove(ini_path)
        ini_contents = "[.ShellClassInfo]\nIconResource=Title.ico,0"
        with open(ini_path, "w") as writer:
            writer.write(ini_contents)
        

        # set icon if system is windows
        if os.name == 'nt':
            try:
                self.__set_icon_on_windows()
            except Exception as e:
                warnings.warn("Unable to set folder icon (%s)"%e)
        elif os.name == 'posix':
            raise Exception('posix system not implemented yet')
        elif os.name == 'mac':
            raise Exception('mac system not implemented yet')
        elif os.name == 'os2':
            raise Exception('os2 system not implemented yet')
        elif os.name == 'ce':
            raise Exception('ce system not implemented yet')
        elif os.name == 'java':
            raise Exception('java system not implemented yet')
        elif os.name == 'riscos':
            raise Exception('riscos system not implemented yet')


    def __set_icon_on_windows(self):
        HICON = c_int
        LPTSTR = LPWSTR
        TCHAR = c_wchar
        MAX_PATH = 260
        FCSM_ICONFILE = 0x00000010
        FCS_FORCEWRITE = 0x00000002
        SHGFI_ICONLOCATION = 0x000001000    


        class GUID(Structure):
            _fields_ = [ ('Data1', DWORD),
                         ('Data2', WORD),
                         ('Data3', WORD),
                         ('Data4', BYTE * 8) ]


        class SHFOLDERCUSTOMSETTINGS(Structure):
            _fields_ = [ ('dwSize', DWORD),
                         ('dwMask', DWORD),
                         ('pvid', POINTER(GUID)),
                         ('pszWebViewTemplate', LPTSTR),
                         ('cchWebViewTemplate', DWORD),
                         ('pszWebViewTemplateVersion', LPTSTR),
                         ('pszInfoTip', LPTSTR),
                         ('cchInfoTip', DWORD),
                         ('pclsid', POINTER(GUID)),
                         ('dwFlags', DWORD),
                         ('pszIconFile', LPTSTR),
                         ('cchIconFile', DWORD),
                         ('iIconIndex', c_int),
                         ('pszLogo', LPTSTR),
                         ('cchLogo', DWORD) ]


        class SHFILEINFO(Structure):
            _fields_ = [ ('hIcon', HICON),
                         ('iIcon', c_int),
                         ('dwAttributes', DWORD),
                         ('szDisplayName', TCHAR * MAX_PATH),
                         ('szTypeName', TCHAR * 80) ]    


        shell32 = ctypes.windll.shell32
        fcs = SHFOLDERCUSTOMSETTINGS()
        fcs.dwSize = sizeof(fcs)
        fcs.dwMask = FCSM_ICONFILE

        if (self.__set_file_name_only == True):
            fcs.pszIconFile = os.path.basename(self.__iconPath)
        else:
            fcs.pszIconFile = self.__iconPath

        fcs.cchIconFile = 0
        fcs.iIconIndex = self.__reset 
        hr = shell32.SHGetSetFolderCustomSettings(byref(fcs), self.__folderPath, FCS_FORCEWRITE)
        if hr:
            raise WindowsError(win32api.FormatMessage(hr))

        sfi = SHFILEINFO()
        hr = shell32.SHGetFileInfoW(self.__folderPath, 0, byref(sfi), sizeof(sfi), SHGFI_ICONLOCATION)
        #if hr == 0:
        #    raise WindowsError(win32api.FormatMessage(hr))

        index = shell32.Shell_GetCachedImageIndexW(sfi.szDisplayName, sfi.iIcon, 0)
        shell32.SHUpdateImageW(sfi.szDisplayName, sfi.iIcon, 0, index)