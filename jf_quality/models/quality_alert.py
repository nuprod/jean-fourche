# -*- coding: utf-8 -*-
from odoo import api, fields, models


class QualityAlert(models.Model):
    _inherit = "quality.alert"

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchase Order",
        index=True,
        readonly=False,
        help="Purchase Order linked to this Quality Alert. "
             "Auto-filled from the related receipt when available.",
    )

    check_id = fields.Many2one(
        comodel_name="quality.check",
        string="Quality Check",
        index=True,
        ondelete="set null",
        help="Quality check that originated this alert, when applicable.",
    )

    # -------------------------
    # ONCHANGE
    # -------------------------

    @api.onchange("picking_id")
    def _onchange_picking_id_autofill_partner_purchase(self):
        """
        UX helper: when selecting a stock picking, auto-fill:
        - partner_id (supplier) if empty
        - purchase_id if empty
        """
        for alert in self:
            if not alert.picking_id:
                continue

            supplier, po = alert._get_supplier_and_po_from_picking(alert.picking_id)

            if supplier and not alert.partner_id:
                alert.partner_id = supplier

            if po and not alert.purchase_id:
                alert.purchase_id = po

    @api.onchange("check_id")
    def _onchange_check_id_prefill_from_check(self):
        """
        IMPORTANT: only prefill when coming from the quality.check 'do_alert' button.
        """
        if not self.env.context.get("from_quality_check_do_alert"):
            return

        for alert in self:
            if not alert.check_id:
                continue
            vals = alert._vals_from_quality_check(alert.check_id, only_if_empty=True)
            for k, v in vals.items():
                setattr(alert, k, v)

    # -------------------------
    # CREATE / WRITE
    # -------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        # Only apply "from check" sync when coming from do_alert
        if self.env.context.get("from_quality_check_do_alert"):
            records._sync_from_quality_check()

        # Picking sync can stay global (it only fills missing fields)
        records._sync_partner_purchase_from_links()

        return records

    def write(self, vals):
        res = super().write(vals)

        # Only apply "from check" sync when coming from do_alert
        if "check_id" in vals and self.env.context.get("from_quality_check_do_alert"):
            self._sync_from_quality_check()

        if "picking_id" in vals:
            self._sync_partner_purchase_from_links()

        return res

    # -------------------------
    # SYNC HELPERS
    # -------------------------

    def _sync_from_quality_check(self):
        for alert in self:
            if not alert.check_id:
                continue
            vals = alert._vals_from_quality_check(alert.check_id, only_if_empty=True)
            if vals:
                super(QualityAlert, alert).write(vals)

    def _sync_partner_purchase_from_links(self):
        for alert in self:
            if not alert.picking_id:
                continue

            supplier, po = alert._get_supplier_and_po_from_picking(alert.picking_id)

            updates = {}
            if supplier and not alert.partner_id:
                updates["partner_id"] = supplier.id
            if po and not alert.purchase_id:
                updates["purchase_id"] = po.id

            if updates:
                super(QualityAlert, alert).write(updates)

    # -------------------------
    # VALUE BUILDERS
    # -------------------------

    def _vals_from_quality_check(self, check, only_if_empty=True):
        self.ensure_one()
        vals = {}

        picking = getattr(check, "picking_id", False)
        if picking and (not only_if_empty or not self.picking_id):
            vals["picking_id"] = picking.id

        supplier = getattr(check, "partner_id", False) or False

        # Derive purchase + supplier from picking if possible
        p_for_po = picking or self.picking_id
        if p_for_po:
            supplier2, po2 = self._get_supplier_and_po_from_picking(p_for_po)
            if po2 and (not only_if_empty or not self.purchase_id):
                vals.setdefault("purchase_id", po2.id)
            if not supplier:
                supplier = supplier2

        if supplier and (not only_if_empty or not self.partner_id):
            vals["partner_id"] = supplier.id

        return vals

    def _get_supplier_and_po_from_picking(self, picking):
        Partner = self.env["res.partner"]
        Purchase = self.env["purchase.order"]

        if not picking:
            return (Partner, Purchase)

        po = getattr(picking, "purchase_id", False)
        if po:
            return (po.partner_id, po)

        move = picking.move_ids.filtered(lambda m: m.purchase_line_id)[:1]
        if move:
            po = move.purchase_line_id.order_id
            if po:
                return (po.partner_id, po)

        return (Partner, Purchase)
