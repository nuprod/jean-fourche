/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import BarcodePickingModel from "@stock_barcode/models/barcode_picking_model";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

const WARNING_STATES = ["draft", "waiting", "confirmed"];

patch(BarcodePickingModel.prototype, {
    setData(data) {
        super.setData(...arguments);
        if (WARNING_STATES.includes(this.record.state)) {
            Promise.resolve().then(() => {
                this.dialogService.add(AlertDialog, {
                    title: _t("Livraison non disponible"),
                    body: _t(
                        "Cette livraison n'est pas encore disponible pour le traitement. " +
                        "Veuillez la confirmer et réserver les produits depuis la vue bureau."
                    ),
                });
            });
        }
    },
});
