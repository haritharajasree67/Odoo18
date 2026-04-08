====================================
Dynamic Bank Cheque Management – Odoo 18
====================================

.. image:: banner.png
   :alt: Dynamic Bank Cheque Management
   :align: center


Overview
--------
**Dynamic Bank Cheque Management** is an Odoo 18 accounting module that simplifies
and automates bank cheque printing and management.
It allows users to configure bank-specific cheque layouts, manage cheque books,
and print cheques directly from vendor payments with complete accuracy.

The module provides a drag-and-drop interface to map cheque fields such as
payee name, date, amount, and amount in words onto the uploaded cheque image.


Key Features
------------
* Enable cheque management directly from Accounting settings
* Maintain bank records with cheque image attachments
* Drag-and-drop configuration of cheque fields on cheque layout
* Manage multiple cheque books with configurable cheque ranges
* Generate and track cheque leaves automatically
* Print cheques directly from vendor payments
* Advance cheque preview before printing
* Automatically update cheque status after printing
* Supports accurate cheque tracking and audit control


Business Benefits
-----------------
This module is ideal for businesses that:

* Frequently issue vendor payments via bank cheques
* Use multiple banks and cheque formats
* Want error-free and aligned cheque printing
* Need better control over cheque books and cheque numbers
* Want to avoid manual cheque writing mistakes
* Require traceability of printed cheques


Usage
-----
1. Navigate to **Accounting** menu.
2. Enable **Cheque Management** from Accounting configuration.
3. Create bank records and upload the corresponding cheque image.
4. Configure cheque attributes by dragging fields like:

   * Payee Name
   * Date
   * Amount
   * Amount in Words

5. Create cheque books by defining cheque number ranges.
6. While creating a vendor payment:

   * Select Payment Type as **Send**
   * Select Payment Method as **Checks**

7. Click **Advance Print Cheque**.
8. Choose the cheque book and cheque number.
9. Preview the cheque and print.
10. Verify printed cheque details from the cheque book page.


Technical Notes
---------------
* Fully integrated with Odoo Accounting module
* No impact on existing payment workflows
* Secure handling of cheque numbers and status
* Supports multiple banks and multiple cheque books
* Compatible with Odoo 18 Community and Enterprise editions


Requirements
------------
* Odoo 18 Community or Enterprise
* Accounting module enabled


License
-------
AGPL-3


Changelog
---------
Version 1.0.0
~~~~~~~~~~~~~
* Initial release
* Bank cheque configuration with drag-and-drop layout
* Cheque book and cheque leaf management
* Direct cheque printing from vendor payments
* Advance cheque preview support
