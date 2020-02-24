# Jupyter Notebooks

Try on <https://mybinder.org/>.  These don't work because the `requirements.txt` refers to some Windows specific stuff.  Sigh.

* Launch in Notebook [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/joejcollins/professor-matic.git/master)
* Launch in Jupyter Lab: [![Binder](http://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/joejcollins/professor-matic.git/master?urlpath=lab)
* Launch in RStudio: [![Binder](http://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/joejcollins/professor-matic.git/master?urlpath=rstudio)

or locally

    mkvirtualenv professor-matic
    pip install -r binder/requirements.txt
    workon professor-matic

Then open a Jupyter note book in VSCode (e.g. \Interview Demos\finger_prints.ipynb), it should format the Jupyter note book automatically

    deactivate
