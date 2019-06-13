# vfxtest

<br>

## What's this about?

This project is about **managing a test suite** for a **Python codebase**
that is used in **multiple contexts**.

**Common contexts found in a VFX production environment are:**

* standalone **Python 2.7**
* standalone **Python 3.x**
* **embedded Python interpreters** inside **DCC's**:
    * ``Maya/mayapy``
    * ``Houdini/hython``
    * ``Nuke``
    * ...
<br><br>

## Where's the benefit?

Doing **Test Driven Development** in Python is fairly straight forward
utilizing packages such as ``unittest`` and ``mock``.

It's also really comfortable to get feedback about code coverage using the
``coverage`` package.

### However...

When a **Python codebase** is used inside multiple contexts that do not know
each other it is quite difficult to gather **accurate metrics** about the
**overall test coverage**.

#### And this is where ``vfxtest`` tries to fill the gap.

**``vfxtest``** is just a thin wrapper around ``unittest``, ``mock`` and
``coverage`` that let's you run a **test suite for each context** and then
presents the **combined code coverage** of all those tests.
<br><br>

## I basically scratched my own itch...

While starting to embrace **TDD** in a **VFX production environment** I had
this need and did not find an obvious existing solution to it.
<br><br>

## Documentation

Soon to be found on **vfxtest.readthedocs.com**. 

Stay tuned... :)
<br><br>

## 'Impostor Syndrome' Disclaimer
I'm really still in my first inning of the whole TDD game.

Therefore I'm fully aware that I probably know barely enough to be dangerous
right now. :)

If there already happens to be an existing go-to solution for this problem out
there on the interwebs, I'd love to know about it!

Also if any part of this could be improved (or makes your eyes bleed) please
give me a heads up! :)
<br><br>

### That said, I hope that somebody will get some benefit out of this!

Everything that encourages and helps **maintaining a test suite** in **VFX** is
valuable, as far as I'm concerned... :)
