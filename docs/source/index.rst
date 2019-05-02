Welcome to idapkg's documentation!
==================================

idapkg is a package manager for IDA Pro utilizing
`IDAUSR env <https://www.hex-rays.com/products/ida/support/idadoc/1375.shtml>`_.

A Package is a collection of plugins, processor, loader modules, and til/sig/ids files. They can be downloaded from `public <https://idapkg.com>`_ / `private <https://github.com/Jinmo/idapkg-api>`_ repos. A package's directory structure is like below:

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

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   pkg



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
