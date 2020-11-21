# wxFormBuilder code override

import fileinput
import os

if __name__ == "__main__":
    fout = open('panels_fix.py', 'w')
    for line in fileinput.input("Panels/panels.py", inplace=True):
        line = line.replace("wx.DATAVIEW", "wx.dataview.DATAVIEW")
        line = line.replace(".AddLabelTool", ".AddTool")
        fout.write(line)
    
    fout.close()
    os.remove('Panels/panels.py')
    os.rename('panels_fix.py', 'Panels/panels.py')

