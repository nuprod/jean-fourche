# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta
from collections import defaultdict

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

    supplier_return_picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Retour fournisseur",
        readonly=True,
        copy=False,
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

    def action_create_supplier_return(self):
        self.ensure_one()

        if self.supplier_return_picking_id:
            return self.action_open_supplier_return()

        if not self.partner_id:
            raise UserError(_("Veuillez renseigner un fournisseur sur l'alerte qualité."))
        if not self.product_id:
            raise UserError(_("Veuillez renseigner un produit sur l'alerte qualité."))
        if self.piece_qty <= 0:
            raise UserError(_("La quantité à retourner doit être strictement positive."))

        picking_type_id = self.env["ir.config_parameter"].sudo().get_param("jf_quality.supplier_return_picking_type_id")
        picking_type = self.env["stock.picking.type"].browse(int(picking_type_id)) if picking_type_id else self.env["stock.picking.type"]
        if not picking_type:
            raise UserError(_("Veuillez configurer le type d'opération de retour fournisseur dans les paramètres."))

        location_dest = self.env.ref("stock.stock_location_suppliers", raise_if_not_found=False)
        if not location_dest:
            raise UserError(_("La localisation fournisseur n'a pas été trouvée."))

        location_src = picking_type.default_location_src_id
        if not location_src:
            raise UserError(_("Le type d'opération configuré doit définir une localisation source."))

        picking = self.env["stock.picking"].create({
            "partner_id": self.partner_id.id,
            "picking_type_id": picking_type.id,
            "location_id": location_src.id,
            "location_dest_id": location_dest.id,
            "origin": self.name,
        })

        move = self.env["stock.move"].create({
            "name": self.product_id.display_name,
            "product_id": self.product_id.id,
            "product_uom_qty": self.piece_qty,
            "product_uom": self.product_id.uom_id.id,
            "picking_id": picking.id,
            "location_id": location_src.id,
            "location_dest_id": location_dest.id,
            "partner_id": self.partner_id.id,
            "origin": self.name,
        })

        move_line_values = self._prepare_supplier_return_move_lines(move, self.piece_qty)
        if move_line_values:
            self.env["stock.move.line"].create(move_line_values)

        self.supplier_return_picking_id = picking

        return self.action_open_supplier_return()

    def action_open_supplier_return(self):
        self.ensure_one()
        if not self.supplier_return_picking_id:
            raise UserError(_("Aucun retour fournisseur n'est lié à cette alerte."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Retour fournisseur"),
            "res_model": "stock.picking",
            "view_mode": "form",
            "res_id": self.supplier_return_picking_id.id,
        }

    def _prepare_supplier_return_move_lines(self, move, qty):
        self.ensure_one()
        product = self.product_id
        tracking = product.tracking
        if tracking == "none":
            return []

        if self.lot_id:
            if tracking == "serial" and qty != 1:
                raise UserError(_("Un produit suivi par numéro de série doit être retourné avec une quantité de 1."))
            return [self._prepare_supplier_return_move_line(move, qty, self.lot_id)]

        done_lines = self.picking_id.move_line_ids.filtered(
            lambda ml: ml.product_id == product and ml.qty_done > 0 and ml.lot_id
        )
        if not done_lines:
            raise UserError(_("Aucun numéro de lot/série trouvé sur la réception d'origine pour ce produit."))

        remaining_qty = float(qty)
        values = []
        aggregated_qty = defaultdict(float)
        serial_ids = []
        for line in done_lines:
            if remaining_qty <= 0:
                break
            line_qty = min(line.qty_done, remaining_qty)
            if tracking == "serial":
                serial_ids.append(line.lot_id)
                remaining_qty -= 1
            else:
                aggregated_qty[line.lot_id] += line_qty
                remaining_qty -= line_qty

        if remaining_qty > 0:
            raise UserError(_("Impossible de préparer le retour: quantité insuffisante avec lot/série sur la réception."))

        if tracking == "serial":
            return [self._prepare_supplier_return_move_line(move, 1, lot) for lot in serial_ids]

        for lot, lot_qty in aggregated_qty.items():
            values.append(self._prepare_supplier_return_move_line(move, lot_qty, lot))
        return values

    def _prepare_supplier_return_move_line(self, move, qty, lot):
        return {
            "move_id": move.id,
            "picking_id": move.picking_id.id,
            "product_id": move.product_id.id,
            "product_uom_id": move.product_uom.id,
            "qty_done": qty,
            "location_id": move.location_id.id,
            "location_dest_id": move.location_dest_id.id,
            "lot_id": lot.id,
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
