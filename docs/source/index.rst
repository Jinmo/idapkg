.. idapkg documentation master file, created by
   sphinx-quickstart on Sun Apr 28 01:52:16 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to idapkg's documentation!
==================================

idapkg is a package manager for IDA Pro. Packages are made of plugins, processor, loader modules, and til/sig/ids files. They can be downloaded from public / private repos.

The package format is same as IDA loads the plugin, except info.json. See IDAUSR variable. See `IDAUSR variable <https://www.hex-rays.com/products/ida/support/idadoc/1375.shtml>`_.

.. code-block :: diff

    Required:
    +   info.json

    Optional for IDA:
    +   plugins/
        ...
    +   procs/
        ...
    +   loaders/
        ...
    +   til/ sig/ ids/
        ...

    Optional for package:
    +   README.md


################
Additional notes
################

`idapkg/packages` is added to `sys.path` at startup, so placing `__init__.py` enables importing your packages in IDAPython.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   pkg



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
