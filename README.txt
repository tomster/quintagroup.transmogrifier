***************************************
Export/import transmogrifier blueprints
***************************************

.. contents::

This package contains blueprints for collective.transmogrifier
pipelines, that may be used to export/import Plone site content.
It also overrides GenericSetup ``Content`` step so this package
can be used out-the-box to migrate site content.

Running test
************

In current state before running all test you need to go to
collective.transmogrifier package and edit configure.zcml file, replacing

::

    <adapter factory=".transmogrifier.Transmogrifier" /> 

line with

::
    <adapter 
        factory=".transmogrifier.Transmogrifier" 
        provides=".interfaces.ITransmogrifier" 
        />

Credits
*******

Design and development

    - Bohdan Koval _ at Quintagroup_
    - Andriy Mylenkyy _ at Quintagroup_
    - Vitaliy Podoba
    - Volodymyr Cherepanyak _ at Quintagroup_
    - Myroslav Opyr _ at Quintagroup_


.. _Quintagroup: http://www.quintagroup.com/
