
import maya.cmds as cmds
import time

import vfxtest

# -----------------------------------------------------------------------------
def runDelayed():

    print '-----------------------------'
    print 'vfxtest: runTestsDelayed()'
    print '-----------------------------'
    stats = vfxtest.runMain()
    # don't quit if errors occured
    if stats['errors'] == 0:
        cmds.quit(f=True)

# -----------------------------------------------------------------------------
def scheduleDelayed():
    print '-----------------------------'
    print 'vfxtest: scheduleDelayed()'
    print '-----------------------------'

    myself = __file__.replace('\\', '/').replace('.pyc', '.py')

    run_delayed = 'import maya.cmds as cmds;'\
                  "cmds.evalDeferred('execfile(\"{}\")')".format(myself)

    cmds.scriptJob(runOnce=True, event=['NewSceneOpened', run_delayed])
    cmds.file(new=True, f=True)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    runDelayed()

