.. image:: https://img.shields.io/badge/licence-OPL--1-blue.svg
   :target: https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html
   :alt: License: OPL-1

==================
Payment Credomatic
==================

This application allows to pay with Credomatic Payment Acquirer

Installation
============

Simply install the module.

Configuration
=============

1. Navigate into Website > Configurations > Payment Acquirers.
2. Find Debit / Credit card (That is Credomatic).
3. Click on activate.
4. Once it's opened, publish it. It's necessary for it to appear in the website.
5. Fill out the credentials section. Witout the correct credentials, the authorization cannot be done, and the payment acquirer will fail.
6. Save the record.

Usage
=====

For the website
---------------

1. Navigate into the Website's shop.
2. Choose a product and add it to your shopping cart.
3. Proceed to the checkout and add your billing information.
4. Once in the payment section, choose "Credit / Debit card" and fill the information to pay.


For the backend sales
---------------------

1. Navigate to Sales
2. Create a quotation.
3. Click the button "Send by email".
4. Click the button "Preview", so you can open that quotation.
5. Choose "Credit / Debit card" and fill the information and pay the quotation.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: http://runbot.vauxoo.com/runbot/repo/git-github-com-vauxoo-vauxoo-apps-3

Known issues / Roadmap
======================

* Better error handling.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Vauxoo/inteco/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/Vauxoo/inteco/issues/new?body=module:%20payment_credomatic%0Aversion:%209.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

This module was created by Vauxoo

Contributors
------------

* Javier Vega <javier@vauxoo.com>
* Oscar Alcala <oscar@vauxoo.com>

Maintainer
----------

.. image:: http://www.vauxoo.com/logo.png
   :alt: Vauxoo.
   :target: http://www.vauxoo.com

This module is maintained by Vauxoo.
