GEODIS Dangerous Goods Integration
=================================

Business test scenario
----------------------

1. Create two products (A and B) and add ADR lines on each with the same ``No ONU`` value ``3481``.
2. Set ``poids_matiere_dangereuse`` to ``2.0`` on product A and ``1.5`` on product B.
3. Create one outgoing picking with two packages.
4. Pack product A quantity ``1`` in package P1 and product B quantity ``2`` in package P2.
5. Validate that ``dangerous_goods_json`` on the picking contains one consolidated ONU line:

   * ``no_onu`` = ``3481``
   * ``nb_emballages`` = ``2`` (P1 + P2)
   * ``poids_volume`` = ``5.0`` (``2.0*1 + 1.5*2``)

6. Trigger GEODIS shipment creation and verify payload ``listMatieresDangereuses`` has one line for ``3481`` with:

   * ``nbEmballages`` = ``2``
   * ``poidsVolume`` = ``5.0``

Notes
-----

* Products not assigned to any package are intentionally excluded from ADR computation.
* ``dangerous_goods_json`` is a debug field only and is never reused as payload input.
