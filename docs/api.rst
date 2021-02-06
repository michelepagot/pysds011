API documentation
=================

.. autosummary::
    pysds011
    pysds011.driver
    pysds011.cli

Driver API
##########
Low level layer that is in charge to manage communication with the sensor. This is the most reusable part of this package

.. automodule:: pysds011.driver
    :members:

CLI app API
###########
Command line interface documentation

.. click:: pysds011.cli:main
  :prog: pysds011
  :nested: full
