# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta

import logging
_logger = logging.getLogger(__name__)


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

    piece_qty = fields.Integer(
        string="Nombre de pièces",
        default=1,
        help="Nombre de pièces concernées par l'alerte.",
    )

    criticality = fields.Selection(
        selection=[
            ("minor", "Mineur / Minor"),
            ("major", "Majeur / Major"),
            ("critical", "Critique / Critical"),
        ],
        string="Niveau de criticité",
        default="minor",
        required=True,
        index=True,
    )

    request_type = fields.Selection(
        selection=[
            ("replacement", "Demande de remplacement / Replacement"),
            ("credit_note", "Demande d’avoir / Credit note"),
        ],
        string="Type de demande",
        index=True,
    )

    supplier_quality_contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="Contact qualité (fournisseur)",
        domain="[('parent_id', '=', partner_id), ('type', 'in', ('contact', 'other'))]",
        help="Contact qualité rattaché au fournisseur (contact enfant).",
    )


    def action_send_quality_alert(self):
        self.ensure_one()

        recipient = self.supplier_quality_contact_id
        if not recipient or not recipient.email:
            raise UserError(_("Veuillez renseigner un contact qualité fournisseur avec email."))

        template = self.env.ref("jf_quality.mail_template_quality_alert", raise_if_not_found=False)
        if not template:
            raise UserError(_("Le modèle d'email de l'alerte qualité est introuvable."))

        compose_form = self.env.ref("mail.email_compose_message_wizard_form", raise_if_not_found=False)
        if not compose_form:
            raise UserError(_("Le formulaire standard de composition d'email est introuvable."))

        followers = self.message_partner_ids.filtered(
            lambda p: p.email and p.id != recipient.id
        )

        ctx = {
            "default_model": self._name,
            "default_res_ids": [self.id],
            "default_composition_mode": "comment",
            "default_template_id": template.id,
            "default_partner_ids": [recipient.id],      # To
            "default_partner_cc_ids": followers.ids,    # CC
            "default_email_layout_xmlid": "mail.mail_notification_light",
            "force_email": True,
        }

        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        if activity_type:
            existing_activity = self.activity_ids.filtered(
                lambda a: a.activity_type_id.id == activity_type.id
                and a.user_id.id == self.env.user.id
                and a.summary == _("Relancer le fournisseur pour l'alerte qualité")
                and not a.date_done
            )
            if not existing_activity:
                self.activity_schedule(
                    activity_type_id=activity_type.id,
                    date_deadline=fields.Date.today() + timedelta(days=7),
                    summary=_("Relancer le fournisseur pour l'alerte qualité"),
                    note=_("Vérifier la réponse du fournisseur suite à l'alerte qualité envoyée."),
                    user_id=self.env.user.id,
                )

        return {
            "type": "ir.actions.act_window",
            "name": _("Envoyer l'alerte qualité"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "views": [(compose_form.id, "form")],
            "target": "new",
            "context": ctx,
        }

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
