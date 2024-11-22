By default, when Odoo encounters a bank statement line ref such as a34bc3xxx1, it
will extract the numerical characters and concatenate them into a numerical token,
eg. 3431 in this case. If then a move line is found that has for example cxxx343y1
as a ref, it will match with this one also: not on the text ref but via the
numerical component.

Sometimes this is not desirable.

This module allows to configure a checkbox on a reconcile model to disable
numerical token matching for this model.
